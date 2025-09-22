import streamlit as st
import sys
import os
import base64
from PIL import Image
import io

# Add core module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from config import Config
from hybrid_classifier import CampusVoiceClassifier

# Page configuration
st.set_page_config(
    page_title="Campus Voice AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .result-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }
    
    .priority-critical { border-left-color: #dc3545 !important; }
    .priority-high { border-left-color: #fd7e14 !important; }
    .priority-medium { border-left-color: #ffc107 !important; }
    .priority-low { border-left-color: #28a745 !important; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
@st.cache_resource
def initialize_system():
    config = Config()
    classifier = CampusVoiceClassifier(config)
    return config, classifier

def encode_image(image_file):
    """Encode uploaded image to base64"""
    try:
        image = Image.open(image_file)
        # Convert to RGB if necessary
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG')
        return base64.b64encode(buffer.getvalue()).decode()
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def main():
    # Initialize system
    config, classifier = initialize_system()
    
    # Initialize session state
    if 'results_history' not in st.session_state:
        st.session_state.results_history = []
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎓 Campus Voice AI v3.0</h1>
        <p>Intelligent Complaint Classification and Routing System</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Department Selection - REQUIRED
        st.subheader("👤 Your Department")
        user_department = st.selectbox(
            "Select your department:",
            config.departments,
            help="This will be used for routing academic complaints"
        )
        
        if not user_department:
            st.error("Please select your department to continue!")
            return
        
        # Model Selection
        st.subheader("🤖 AI Model Selection")
        
        # Get available models
        available_models = classifier.llm_client.available_models
        text_models = [m for m in available_models if any(tm in m for tm in config.text_models)]
        multimodal_models = [m for m in available_models if any(mm in m for mm in config.multimodal_models)]
        
        # Model type selection
        model_type = st.radio(
            "Choose model type:",
            ["📝 Text-only", "🖼️ Multimodal (with image support)"],
            help="Multimodal models can analyze both text and images"
        )
        
        # Model selection based on type
        if model_type == "📝 Text-only":
            if text_models:
                selected_model = st.selectbox("Text Model:", text_models)
                classifier.llm_client.set_model(selected_model, is_multimodal=False)
                st.success(f"✅ Using: {selected_model}")
            else:
                st.error("❌ No text models available!")
                st.info("Make sure Ollama is running with models installed")
                return
        else:
            if multimodal_models:
                selected_model = st.selectbox("Multimodal Model:", multimodal_models)
                classifier.llm_client.set_model(selected_model, is_multimodal=True)
                st.success(f"✅ Using: {selected_model}")
                st.info("🖼️ Image upload will be enabled")
            else:
                st.error("❌ No multimodal models available!")
                st.info("Install LLaVA: `ollama pull llava:latest`")
                return
        
        # System Information
        st.subheader("📊 System Info")
        st.info(f"""
        **Department**: {user_department}
        **Model Type**: {model_type}
        **Available Models**: {len(available_models)}
        **Multimodal**: {'✅' if config.is_multimodal else '❌'}
        """)
    
    # Main Content Area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Submit Your Complaint")
        
        # Complaint Text Input
        complaint_text = st.text_area(
            "Describe your complaint:",
            height=120,
            placeholder="Please describe your issue in detail. Be specific about what happened, when, and where.",
            help="Provide as much detail as possible for accurate classification"
        )
        
        # Image Upload Section (only if multimodal model selected)
        uploaded_image = None
        if config.is_multimodal:
            st.subheader("🖼️ Visual Evidence (Optional)")
            
            # File uploader with drag and drop
            uploaded_image = st.file_uploader(
                "Drag and drop an image here or click to browse",
                type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
                help="Upload screenshots, photos, or any visual evidence related to your complaint"
            )
            
            if uploaded_image:
                # Display the uploaded image
                col_img1, col_img2 = st.columns([1, 2])
                with col_img1:
                    st.image(uploaded_image, caption="Uploaded Image", width=200)
                with col_img2:
                    st.success("✅ Image uploaded successfully!")
                    st.info(f"📄 **File**: {uploaded_image.name}")
                    st.info(f"📏 **Size**: {uploaded_image.size} bytes")
        
        # Additional Input Fields
        col_upvotes, col_submit = st.columns([1, 1])
        
        with col_upvotes:
            upvotes = st.number_input(
                "👍 Community Upvotes:",
                min_value=0,
                value=0,
                help="Number of upvotes this complaint has received from the community"
            )
        
        with col_submit:
            st.write("")  # Spacing
            submit_button = st.button(
                "🚀 Classify & Route Complaint",
                type="primary",
                help="Click to analyze and route your complaint"
            )
    
    with col2:
        st.header("📚 Quick Guide")
        
        # Authority Categories
        with st.expander("🏢 Authority Categories", expanded=True):
            st.markdown("""
            **🏠 Hostel**: Accommodation, mess, rooms, facilities
            - Normal: → Warden
            - Against Warden: → Deputy Warden  
            - Against Deputy: → Senior Deputy Warden
            
            **📚 Academic**: Classes, exams, faculty, curriculum
            - Always routes to your department's HOD
            
            **🏗️ Infrastructure**: Buildings, systems, maintenance
            - Always routes to Administrative Officer (AO)
            """)
        
        # Examples
        with st.expander("📝 Example Complaints"):
            st.markdown("""
            **Hostel Examples:**
            - "Mess food quality is poor"
            - "Warden is not responding to requests" ⚠️
            
            **Academic Examples:**
            - "Professor cancelled classes without notice"
            - "Lab equipment not working"
            
            **Infrastructure Examples:**
            - "Library WiFi constantly down"
            - "Biometric system malfunctioning"
            """)
        
        # Priority Information
        with st.expander("⚡ Priority Levels"):
            st.markdown("""
            🔴 **Critical**: Harassment, safety issues, corruption
            🟠 **High**: Urgent matters, significant problems
            🟡 **Medium**: Important but not urgent
            🟢 **Low**: General complaints, suggestions
            """)
    
    # Process Complaint
    if submit_button:
        if not complaint_text.strip():
            st.error("⚠️ Please enter a complaint description!")
            return
        
        with st.spinner("🔄 Analyzing complaint..."):
            try:
                # Encode image if provided
                image_data = None
                if uploaded_image and config.is_multimodal:
                    image_data = encode_image(uploaded_image)
                    if not image_data:
                        st.warning("⚠️ Failed to process image, continuing with text-only analysis")
                
                # Classify the complaint
                result = classifier.classify(
                    complaint=complaint_text,
                    user_department=user_department,
                    upvotes=upvotes,
                    image_data=image_data
                )
                
                # Store in history
                st.session_state.results_history.append(result)
                
                # Display results
                display_results(result, user_department)
                
            except Exception as e:
                st.error(f"❌ An error occurred during classification: {str(e)}")
                st.info("Please check if Ollama is running and try again")
    
    # Results History
    if st.session_state.results_history:
        st.header("📊 Recent Classifications")
        
        # Show last 3 results
        for i, result in enumerate(reversed(st.session_state.results_history[-3:])):
            idx = len(st.session_state.results_history) - i
            with st.expander(f"Complaint #{idx}: {result.category.title()} - {result.priority_level.title()} Priority"):
                display_results(result, user_department, compact=True)

def display_results(result, user_department, compact=False):
    """Display classification results in a formatted way"""
    
    # Priority color mapping
    priority_colors = {
        'critical': '#dc3545',
        'high': '#fd7e14', 
        'medium': '#ffc107',
        'low': '#28a745'
    }
    
    priority_icons = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡', 
        'low': '🟢'
    }
    
    if not compact:
        st.success("✅ Classification Complete!")
    
    # Create result card
    priority_class = f"priority-{result.priority_level}"
    
    st.markdown(f"""
    <div class="result-card {priority_class}">
        <h3>📋 Classification Results</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Main metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🏢 Category",
            result.category.title(),
            help=f"Complaint classified as {result.category}"
        )
    
    with col2:
        priority_display = f"{priority_icons[result.priority_level]} {result.priority_level.title()}"
        st.metric(
            "⚡ Priority", 
            priority_display,
            help=f"Priority level: {result.priority_level}"
        )
    
    with col3:
        confidence_icon = "🟢" if result.confidence == "high" else "🟡" if result.confidence == "medium" else "🔴"
        st.metric(
            "🧠 Confidence",
            f"{confidence_icon} {result.confidence.title()}",
            help=f"AI confidence: {result.confidence}"
        )
    
    with col4:
        bypass_icon = "🔄" if result.bypass_applied else "📍"
        st.metric(
            "🎯 Routing",
            f"{bypass_icon} {'Bypass' if result.bypass_applied else 'Direct'}",
            help="Whether authority bypass was applied"
        )
    
    # Detailed Information
    if not compact:
        # Final Authority (prominent display)
        st.subheader("🎯 Final Authority")
        st.success(f"**{result.final_authority}**")
        
        # Routing Path
        st.subheader("📋 Routing Details")
        for step in result.routing_path:
            st.write(f"• {step}")
        
        # Bypass Warning (if applicable)
        if result.bypass_applied:
            st.warning("🔄 **Authority Bypass Applied** - Complaint routed to avoid conflict of interest")
        
        # Analysis & Reasoning  
        st.subheader("💭 Analysis")
        st.write(result.reasoning)
        
        # Technical Details
        with st.expander("🔧 Technical Details"):
            col_tech1, col_tech2 = st.columns(2)
            
            with col_tech1:
                st.write(f"**Model Used**: {result.model_used}")
                st.write(f"**Processing Time**: {result.processing_time:.2f}s")
                st.write(f"**User Department**: {user_department}")
            
            with col_tech2:
                st.write(f"**Image Analysis**: {'Yes' if result.used_image else 'No'}")
                st.write(f"**Community Upvotes**: {result.upvotes}")
                
                # Priority breakdown
                if 'factors' in result.detailed_analysis.get('priority', {}):
                    factors = result.detailed_analysis['priority']['factors']
                    st.write("**Priority Factors**:")
                    for factor, info in factors.items():
                        if info['score'] > 0:
                            st.write(f"  - {factor}: {info['score']:.2f}")

if __name__ == "__main__":
    main()
