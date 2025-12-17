"""
CampusVoice - Student Complaint Management System
Streamlit Web Interface - Version 4.0.0

Features:
- Submit complaints with smart image detection
- Browse public complaints & vote
- View student dashboard
- Authority portal
- Real-time statistics
- Test advanced scenarios
"""

import streamlit as st
import requests
import json
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List

# =================== CONFIGURATION ===================

API_BASE_URL = "http://localhost:5000/api/v1"
TIMEOUT = 30

# Page configuration
st.set_page_config(
    page_title="CampusVoice - Smart Complaint System",
    page_icon="📢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .complaint-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# =================== API FUNCTIONS ===================

def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_departments():
    """Get list of departments."""
    try:
        response = requests.get(f"{API_BASE_URL}/config/departments", timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()['data']['departments']
        return []
    except:
        return []

def check_image_requirement(complaint_text):
    """Check if image is required for complaint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/complaints/check-image-requirement",
            json={"complaint_text": complaint_text},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def submit_complaint(complaint_data):
    """Submit a complaint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/complaints",
            json=complaint_data,
            timeout=TIMEOUT
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e)}

def get_student_complaints(roll_number, page=1, limit=10):
    """Get complaints by student."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/complaints/student/{roll_number}",
            params={"page": page, "limit": limit},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def get_public_complaints(page=1, limit=10, sort_by="created_at"):
    """Get public complaints."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/complaints/public",
            params={"page": page, "limit": limit, "sort_by": sort_by},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def vote_on_complaint(complaint_id, roll_number, vote_type):
    """Vote on a complaint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/complaints/{complaint_id}/vote",
            json={"roll_number": roll_number, "vote_type": vote_type},
            timeout=TIMEOUT
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e)}

def get_complaint_by_id(complaint_id):
    """Get single complaint details."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/complaints/{complaint_id}",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def get_system_statistics():
    """Get system statistics."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/statistics/system",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

def get_authority_complaints(authority_name, page=1, limit=10):
    """Get complaints by authority."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/complaints/authority/{authority_name}",
            params={"page": page, "limit": limit},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['data']
        return None
    except:
        return None

# =================== HELPER FUNCTIONS ===================

def display_complaint_card(complaint, show_voter_controls=False, voter_roll=None):
    """Display a complaint card - FIXED VERSION."""
    with st.container():
        st.markdown('<div class="complaint-card">', unsafe_allow_html=True)
        
        # Header
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**🆔 ID:** `{complaint.get('complaint_id', 'N/A')}`")
        with col2:
            priority_color = {
                'Critical': '🔴',
                'High': '🟠',
                'Medium': '🟡',
                'Low': '🟢'
            }
            priority = complaint.get('priority_level', 'Unknown')
            st.markdown(f"{priority_color.get(priority, '⚪')} **{priority}**")
        with col3:
            status_emoji = {
                'raised': '🆕',
                'opened': '👁️',
                'reviewed': '🔍',
                'closed': '✅'
            }
            status = complaint.get('status', 'unknown')
            st.markdown(f"{status_emoji.get(status, '❓')} {status.title()}")
        
        # Content
        category = complaint.get('category', 'unknown')
        st.markdown(f"**📂 Category:** {category.title()}")
        
        authority = complaint.get('assigned_authority', 'Not assigned')
        st.markdown(f"**👤 Authority:** {authority}")
        
        st.markdown(f"**💬 Complaint:**")
        
        # ✅ FIX: Handle different field names
        complaint_text = (
            complaint.get('rephrased_complaint') or 
            complaint.get('complaint_text') or 
            complaint.get('original_complaint') or
            "No complaint text available"
        )
        st.write(complaint_text)
        
        # Metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            created_at = complaint.get('created_at', 'N/A')
            if created_at != 'N/A':
                created_at = created_at[:10] if len(created_at) > 10 else created_at
            st.caption(f"📅 Created: {created_at}")
        with col2:
            if 'upvotes' in complaint or 'net_votes' in complaint:
                upvotes = complaint.get('upvotes', 0)
                downvotes = complaint.get('downvotes', 0)
                net_votes = complaint.get('net_votes', upvotes - downvotes)
                st.caption(f"👍 {upvotes} | 👎 {downvotes} | Net: {net_votes}")
        with col3:
            is_public = complaint.get('is_public', False)
            visibility = "🌍 Public" if is_public else "🔒 Private"
            st.caption(visibility)
        
        # Voting controls
        if show_voter_controls and voter_roll and is_public:
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("👍 Upvote", key=f"up_{complaint['complaint_id']}"):
                    status, result = vote_on_complaint(complaint['complaint_id'], voter_roll, 'upvote')
                    if status == 200:
                        st.success("✅ Upvoted!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        error_msg = result.get('error', result.get('message', 'Failed'))
                        st.error(f"❌ {error_msg}")
            with col2:
                if st.button("👎 Downvote", key=f"down_{complaint['complaint_id']}"):
                    status, result = vote_on_complaint(complaint['complaint_id'], voter_roll, 'downvote')
                    if status == 200:
                        st.success("✅ Downvoted!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        error_msg = result.get('error', result.get('message', 'Failed'))
                        st.error(f"❌ {error_msg}")
        
        st.markdown('</div>', unsafe_allow_html=True)

def format_priority_badge(priority):
    """Format priority as colored badge."""
    colors = {
        'Critical': 'red',
        'High': 'orange',
        'Medium': 'yellow',
        'Low': 'green'
    }
    color = colors.get(priority, 'gray')
    return f'<span style="background-color:{color};color:white;padding:0.2rem 0.5rem;border-radius:5px;font-weight:bold;">{priority}</span>'

# =================== PAGE: HOME ===================

def page_home():
    """Home page with system overview."""
    st.markdown('<p class="main-header">📢 CampusVoice - Smart Complaint System</p>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("🔴 **API Server is not running!** Please start the server with `python main.py`")
        return
    
    st.success("🟢 **System Online** - AI-Powered Complaint Management")
    
    # System info
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Key Features")
        st.markdown("""
        - ✅ **Smart Image Detection** - AI determines if visual evidence is needed
        - 🤖 **Professional Rephrasing** - Converts casual text to formal complaints
        - 🎯 **Intelligent Routing** - Auto-assigns to correct authority
        - 🔒 **Privacy Protection** - Sensitive complaints handled confidentially
        - ⚡ **Priority Scoring** - Critical issues get immediate attention
        - 🗳️ **Community Voting** - Students can support important issues
        - 📊 **Real-time Analytics** - Track system performance
        """)
    
    with col2:
        st.markdown("### 🚀 Quick Start")
        st.markdown("""
        **For Students:**
        1. Go to **📝 Submit Complaint** page
        2. Fill in your details and complaint
        3. Submit and track progress
        
        **Browse Public Issues:**
        1. Visit **🌍 Public Feed** page
        2. View all public complaints
        3. Vote on issues that matter
        
        **For Authorities:**
        1. Go to **👔 Authority Portal**
        2. View assigned complaints
        3. Update status and resolution
        """)
    
    # Statistics
    st.markdown("---")
    st.markdown("### 📊 System Statistics")
    
    stats = get_system_statistics()
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Complaints", stats.get('total_complaints', 0))
        with col2:
            st.metric("Public", stats.get('public_complaints', 0))
        with col3:
            st.metric("Raised", stats.get('raised_count', 0))
        with col4:
            st.metric("Resolved", stats.get('closed_count', 0))
        
        # Category breakdown
        if stats.get('by_category'):
            st.markdown("#### 📂 Complaints by Category")
            df_cat = pd.DataFrame([
                {'Category': cat.title(), 'Count': count}
                for cat, count in stats['by_category'].items()
            ])
            if not df_cat.empty:
                fig = px.bar(df_cat, x='Category', y='Count', color='Category')
                st.plotly_chart(fig, use_container_width=True)

# =================== PAGE: SUBMIT COMPLAINT ===================

def page_submit_complaint():
    """Submit complaint page."""
    st.markdown('<p class="main-header">📝 Submit Complaint</p>', unsafe_allow_html=True)
    
    if not check_api_health():
        st.error("🔴 API Server is not running!")
        return
    
    departments = get_departments()
    if not departments:
        st.error("❌ Failed to load departments")
        return
    
    with st.form("complaint_form"):
        st.markdown("### 👤 Student Information")
        
        col1, col2 = st.columns(2)
        with col1:
            roll_number = st.text_input("Roll Number *", placeholder="21CS001")
            department = st.selectbox("Department *", departments)
        with col2:
            gender = st.selectbox("Gender *", ["male", "female", "other"])
            residence = st.selectbox("Residence *", ["Day Scholar", "Hostel A", "Hostel B", "Hostel C"])
        
        st.markdown("### 💬 Complaint Details")
        
        complaint_text = st.text_area(
            "Describe your complaint *",
            placeholder="Explain your issue in detail...",
            height=150,
            help="Be specific and provide all relevant details"
        )
        
        # Smart image detection
        if complaint_text and len(complaint_text) > 20:
            with st.spinner("🔍 Checking if image is required..."):
                img_check = check_image_requirement(complaint_text)
                if img_check:
                    if img_check.get('is_mandatory'):
                        st.error(f"📸 **Image Required:** {img_check.get('reason')}")
                    elif img_check.get('needs_image'):
                        st.warning(f"📸 **Image Recommended:** {img_check.get('reason')}")
                    else:
                        st.info(f"ℹ️ **No image needed:** {img_check.get('reason')}")
        
        is_public = st.checkbox(
            "Make this complaint public",
            value=True,
            help="Public complaints can be viewed and voted on by other students"
        )
        
        submit_button = st.form_submit_button("🚀 Submit Complaint", use_container_width=True)
        
        if submit_button:
            # Validate
            if not all([roll_number, department, gender, residence, complaint_text]):
                st.error("❌ Please fill all required fields!")
                return
            
            if len(complaint_text) < 20:
                st.error("❌ Complaint text must be at least 20 characters!")
                return
            
            # Submit
            complaint_data = {
                "roll_number": roll_number,
                "department": department,
                "gender": gender,
                "residence": residence,
                "complaint_text": complaint_text,
                "is_public": is_public
            }
            
            with st.spinner("🔄 Processing your complaint..."):
                status, result = submit_complaint(complaint_data)
            
            if status == 201:
                data = result.get('data', {})
                st.balloons()
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.success("✅ **Complaint Submitted Successfully!**")
                st.markdown(f"""
                - **Complaint ID:** `{data.get('complaint_id')}`
                - **Category:** {data.get('category', 'N/A').title()}
                - **Assigned To:** {data.get('assigned_authority', 'N/A')}
                - **Priority:** {data.get('priority_level', 'N/A')} (Score: {data.get('priority_score', 0)})
                - **Status:** {data.get('status', 'N/A').title()}
                - **Processing Time:** {data.get('processing_time', 0):.2f}s
                """)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.info("💡 You can track your complaint in the **Student Dashboard** page")
            else:
                st.markdown('<div class="error-box">', unsafe_allow_html=True)
                st.error(f"❌ **Submission Failed:** {result.get('error', 'Unknown error')}")
                if 'details' in result:
                    st.json(result['details'])
                st.markdown('</div>', unsafe_allow_html=True)

# =================== PAGE: STUDENT DASHBOARD ===================

def page_student_dashboard():
    """Student dashboard to view their complaints."""
    st.markdown('<p class="main-header">👤 Student Dashboard</p>', unsafe_allow_html=True)
    
    if not check_api_health():
        st.error("🔴 API Server is not running!")
        return
    
    roll_number = st.text_input("Enter Your Roll Number", placeholder="21CS001")
    
    if roll_number:
        with st.spinner("Loading your complaints..."):
            data = get_student_complaints(roll_number)
        
        if data:
            total = data.get('pagination', {}).get('total', 0)
            st.markdown(f"### 📋 Your Complaints ({total} total)")
            
            complaints = data.get('complaints', [])
            if complaints:
                for complaint in complaints:
                    display_complaint_card(complaint)
            else:
                st.info("📭 No complaints found. Submit your first complaint!")
        else:
            st.error("❌ Failed to load complaints")

# =================== PAGE: PUBLIC FEED ===================

def page_public_feed():
    """Public feed with voting."""
    st.markdown('<p class="main-header">🌍 Public Complaints Feed</p>', unsafe_allow_html=True)
    
    if not check_api_health():
        st.error("🔴 API Server is not running!")
        return
    
    # Voter roll number
    voter_roll = st.text_input("Your Roll Number (for voting)", placeholder="21CS999", help="Enter a valid roll number like 21CS999")
    
    # Sorting
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📢 All Public Complaints")
    with col2:
        sort_by = st.selectbox("Sort By", ["created_at", "net_votes", "priority_score"])
    
    with st.spinner("Loading public complaints..."):
        data = get_public_complaints(sort_by=sort_by, limit=20)
    
    if data:
        total = data.get('pagination', {}).get('total', 0)
        shown = len(data.get('complaints', []))
        st.info(f"Showing {shown} of {total} public complaints")
        
        complaints = data.get('complaints', [])
        if complaints:
            for complaint in complaints:
                display_complaint_card(complaint, show_voter_controls=True, voter_roll=voter_roll)
        else:
            st.warning("📭 No public complaints found")
    else:
        st.error("❌ Failed to load complaints")

# =================== PAGE: AUTHORITY PORTAL ===================

def page_authority_portal():
    """Authority portal to view assigned complaints."""
    st.markdown('<p class="main-header">👔 Authority Portal</p>', unsafe_allow_html=True)
    
    if not check_api_health():
        st.error("🔴 API Server is not running!")
        return
    
    authorities = [
        "Principal",
        "Administrative Officer (AO)",
        "Hostel Warden",
        "Student Counselor / Disciplinary Committee",
        "Head of Department - Computer Science & Engineering",
        "Head of Department - Electronics & Communication Engineering",
        "Head of Department - Mechanical Engineering",
        "Head of Department - Information Technology",
        "Head of Department - Artificial Intelligence and Data Science"
    ]
    
    authority_name = st.selectbox("Select Authority", authorities)
    
    if st.button("🔍 View My Complaints", type="primary"):
        with st.spinner(f"Loading complaints for {authority_name}..."):
            data = get_authority_complaints(authority_name)
        
        if data:
            total = data.get('pagination', {}).get('total', 0)
            st.markdown(f"### 📋 Complaints Assigned to {authority_name}")
            st.info(f"Total: {total} complaints")
            
            complaints = data.get('complaints', [])
            if complaints:
                for complaint in complaints:
                    display_complaint_card(complaint)
            else:
                st.success("✅ No pending complaints!")
        else:
            st.error("❌ Failed to load complaints")

# =================== PAGE: STATISTICS ===================

def page_statistics():
    """Statistics and analytics page."""
    st.markdown('<p class="main-header">📊 System Analytics</p>', unsafe_allow_html=True)
    
    if not check_api_health():
        st.error("🔴 API Server is not running!")
        return
    
    with st.spinner("Loading statistics..."):
        stats = get_system_statistics()
    
    if not stats:
        st.error("❌ Failed to load statistics")
        return
    
    # Overview metrics
    st.markdown("### 📈 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats.get("total_complaints", 0)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Total Complaints</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats.get("raised_count", 0)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Raised</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats.get("reviewed_count", 0)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Reviewed</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-number">{stats.get("closed_count", 0)}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Resolved</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Category breakdown
    if stats.get('by_category'):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📂 By Category")
            df_cat = pd.DataFrame([
                {'Category': cat.title(), 'Count': count}
                for cat, count in stats['by_category'].items()
            ])
            if not df_cat.empty:
                fig = px.pie(df_cat, values='Count', names='Category', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 By Status")
            status_data = {
                'Raised': stats.get('raised_count', 0),
                'Opened': stats.get('opened_count', 0),
                'Reviewed': stats.get('reviewed_count', 0),
                'Closed': stats.get('closed_count', 0)
            }
            df_status = pd.DataFrame([
                {'Status': k, 'Count': v}
                for k, v in status_data.items() if v > 0
            ])
            if not df_status.empty:
                fig = px.bar(df_status, x='Status', y='Count', color='Status')
                st.plotly_chart(fig, use_container_width=True)
    
    # Priority distribution
    if stats.get('by_priority'):
        st.markdown("### ⚡ Priority Distribution")
        df_priority = pd.DataFrame([
            {'Priority': pri.title(), 'Count': count}
            for pri, count in stats['by_priority'].items()
        ])
        if not df_priority.empty:
            fig = px.bar(df_priority, x='Priority', y='Count', color='Priority',
                        color_discrete_map={'Critical': 'red', 'High': 'orange', 'Medium': 'yellow', 'Low': 'green'})
            st.plotly_chart(fig, use_container_width=True)

# =================== PAGE: TEST SCENARIOS ===================

def page_test_scenarios():
    """Test advanced scenarios."""
    st.markdown('<p class="main-header">🧪 Test Advanced Scenarios</p>', unsafe_allow_html=True)
    
    if not check_api_health():
        st.error("🔴 API Server is not running!")
        return
    
    st.info("💡 **Test different complaint types to see intelligent routing in action!**")
    
    # Predefined test scenarios
    scenarios = {
        "🚨 Ragging Complaint": {
            "complaint_text": "I am being ragged by senior students in hostel. They force me to do their work and threaten me if I refuse. This is happening daily and affecting my mental health.",
            "expected_authority": "Principal",
            "expected_visibility": "Confidential"
        },
        "⚠️ Sexual Harassment": {
            "complaint_text": "A professor made inappropriate comments about my appearance and touched my shoulder inappropriately during lab session. I feel very uncomfortable.",
            "expected_authority": "Principal",
            "expected_visibility": "Confidential"
        },
        "🏛️ Cross-Department Issue": {
            "complaint_text": "The main gate security is very poor. Anyone can enter campus without proper checking. This is a safety issue for all departments.",
            "expected_authority": "Administrative Officer (AO)",
            "expected_visibility": "Public"
        },
        "💊 Mental Health Crisis": {
            "complaint_text": "I am feeling very depressed and anxious. The academic pressure is too much and I am having suicidal thoughts. Need counseling support urgently.",
            "expected_authority": "Student Counselor / Principal",
            "expected_visibility": "Confidential"
        },
        "🏠 Hostel Issue": {
            "complaint_text": "The hostel room cleaning is not done properly. Bathrooms are dirty and not maintained.",
            "expected_authority": "Hostel Warden",
            "expected_visibility": "Public"
        },
        "📚 Department Academic": {
            "complaint_text": "The syllabus for Digital Signal Processing course is outdated. Industry requires knowledge of modern DSP tools.",
            "expected_authority": "Head of Department",
            "expected_visibility": "Public"
        }
    }
    
    selected_scenario = st.selectbox("Select Test Scenario", list(scenarios.keys()))
    scenario = scenarios[selected_scenario]
    
    st.markdown("### 📝 Scenario Details")
    st.text_area("Complaint Text", scenario['complaint_text'], height=100, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Expected Authority:** {scenario['expected_authority']}")
    with col2:
        st.markdown(f"**Expected Visibility:** {scenario['expected_visibility']}")
    
    # Input test student details
    st.markdown("### 👤 Test Student Info")
    col1, col2 = st.columns(2)
    with col1:
        test_roll = st.text_input("Roll Number", "21TEST001")
        test_dept = st.selectbox("Department", get_departments() or ["Computer Science & Engineering"])
    with col2:
        test_gender = st.selectbox("Gender", ["male", "female", "other"])
        test_residence = st.selectbox("Residence", ["Hostel A", "Hostel B", "Hostel C", "Day Scholar"])
    
    if st.button("🚀 Run Test", type="primary", use_container_width=True):
        complaint_data = {
            "roll_number": test_roll,
            "department": test_dept,
            "gender": test_gender,
            "residence": test_residence,
            "complaint_text": scenario['complaint_text'],
            "is_public": scenario['expected_visibility'] == "Public"
        }
        
        with st.spinner("🔄 Processing test scenario..."):
            status, result = submit_complaint(complaint_data)
        
        if status == 201:
            data = result.get('data', {})
            st.success("✅ **Test Completed!**")
            
            # Results comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 Expected Results")
                st.markdown(f"- **Authority:** {scenario['expected_authority']}")
                st.markdown(f"- **Visibility:** {scenario['expected_visibility']}")
            
            with col2:
                st.markdown("### 📊 Actual Results")
                st.markdown(f"- **Authority:** {data.get('assigned_authority', 'N/A')}")
                st.markdown(f"- **Visibility:** {'Public' if data.get('is_public') else 'Private/Confidential'}")
                st.markdown(f"- **Category:** {data.get('category', 'N/A').title()}")
                st.markdown(f"- **Priority:** {data.get('priority_level', 'N/A')} ({data.get('priority_score', 0)})")
            
            # Validation
            st.markdown("### ✅ Validation")
            assigned_auth = data.get('assigned_authority', '').lower()
            expected_auth = scenario['expected_authority'].lower()
            authority_match = expected_auth in assigned_auth
            
            is_public = data.get('is_public', False)
            visibility_match = (scenario['expected_visibility'] == "Public" and is_public) or \
                             (scenario['expected_visibility'] == "Confidential" and not is_public)
            
            if authority_match:
                st.success("✅ Authority routing is correct!")
            else:
                st.warning(f"⚠️ Authority mismatch (may still be valid based on LLM decision)")
            
            if visibility_match:
                st.success("✅ Visibility determination is correct!")
            else:
                st.warning("⚠️ Visibility mismatch")
            
            st.markdown(f"**Complaint ID:** `{data.get('complaint_id', 'N/A')}`")
        else:
            st.error(f"❌ Test failed: {result.get('error', 'Unknown error')}")

# =================== MAIN APP ===================

def main():
    """Main application."""
    
    # Sidebar navigation
    st.sidebar.image("https://img.icons8.com/color/96/000000/megaphone.png", width=100)
    st.sidebar.title("Navigation")
    
    pages = {
        "🏠 Home": page_home,
        "📝 Submit Complaint": page_submit_complaint,
        "👤 Student Dashboard": page_student_dashboard,
        "🌍 Public Feed": page_public_feed,
        "👔 Authority Portal": page_authority_portal,
        "📊 Statistics": page_statistics,
        "🧪 Test Scenarios": page_test_scenarios
    }
    
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔧 System Info")
    
    if check_api_health():
        st.sidebar.success("🟢 API Online")
    else:
        st.sidebar.error("🔴 API Offline")
    
    st.sidebar.markdown(f"**Version:** 4.0.0")
    st.sidebar.markdown(f"**LLM:** Groq (llama-3.3-70b)")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Quick Guide")
    st.sidebar.markdown("1. Submit complaints")
    st.sidebar.markdown("2. Track in dashboard")
    st.sidebar.markdown("3. Vote on public issues")
    st.sidebar.markdown("4. Test AI routing")
    
    # Run selected page
    pages[selection]()

if __name__ == "__main__":
    main()
