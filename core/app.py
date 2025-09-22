# 🎓 Campus Voice AI v4.0

import os
import sys
import io
import base64
from typing import Optional, List, Dict, Any

import streamlit as st
from PIL import Image

# Ensure core modules are importable if organized in ./core
sys.path.insert(0, os.path.dirname(__file__))

from config import Config
from hybrid_classifier import CampusVoiceClassifier
from llm_engine import OllamaClient
from privacy_detector import PrivacyDetector
from authority_mapper import AuthorityMapper

# ----------- Streamlit Page Setup -----------
st.set_page_config(
    page_title="Campus Voice AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Basic CSS
st.markdown("""
<style>
.small { font-size: 0.9rem; color: #555; }
.codeblock { background: #0f1117; color: #e6edf3; padding: 0.75rem; border-radius: 8px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 6px; background: #eef2ff; color: #3949ab; margin-right: 0.5rem; }
.route { padding: 0.35rem 0.6rem; border-left: 4px solid #3949ab; background: #f8faff; margin: 0.3rem 0; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ----------- Helpers -----------
@st.cache_resource
def get_services():
    cfg = Config()
    llm = OllamaClient(cfg)
    clf = CampusVoiceClassifier(cfg)
    priv = PrivacyDetector(cfg)
    mapper = AuthorityMapper(cfg)
    return cfg, llm, clf, priv, mapper

def encode_image_to_base64(file) -> Optional[str]:
    try:
        img = Image.open(file)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        st.error(f"Image processing error: {e}")
        return None

def as_badge(text: str) -> str:
    return f'<span class="badge">{text}</span>'

def show_routing_path(path: List[str]):
    for p in path:
        st.markdown(f'<div class="route">{p}</div>', unsafe_allow_html=True)

# ----------- App Body -----------
def main():
    cfg, llm, classifier, privacy, mapper = get_services()

    if "submitted_items" not in st.session_state:
        st.session_state.submitted_items = []
    if "draft" not in st.session_state:
        st.session_state.draft = None

    st.title("Campus Voice AI")
    st.caption("Intelligent complaint classification, rephrasing, and routing")

    # Sidebar: Model & Mode selection
    with st.sidebar:
        st.subheader("Mode & Model")
        input_mode = st.radio(
            "Input mode",
            ["Text only", "Multimodal (text + images)"],
            help="Choose multimodal to add images for analysis"
        )
        is_multimodal = input_mode.startswith("Multimodal")
        cfg.is_multimodal = is_multimodal

        if is_multimodal:
            model = st.selectbox(
                "Multimodal model",
                cfg.multimodal_models,
                index=0
            )
        else:
            model = st.selectbox(
                "Text model",
                cfg.text_models,
                index=0
            )
        cfg.current_model = model

        st.divider()
        st.markdown("System routes:")
        st.markdown("- Hostel → Warden by default; bypass when complaint targets Warden/Deputy Warden")  # routing info
        st.markdown("- Academics → Complainant’s department HoD")
        st.markdown("- Infrastructure → Administrative Officer (AO)")

    # Profile first
    st.subheader("Student Profile")
    col1, col2, col3 = st.columns(3)
    with col1:
        department = st.selectbox(
            "Department",
            cfg.departments,
            help="Academic complaints default to this department unless another is explicitly specified"
        )
    with col2:
        gender = st.selectbox(
            "Gender",
            ["Male", "Female", "Other", "Prefer not to say"]
        )
    with col3:
        residential = st.selectbox(
            "Residence",
            ["Hosteller", "Day Scholar"]
        )

    st.subheader("Complaint Input")
    complaint_text = st.text_area(
        "Describe the complaint in detail",
        height=160,
        placeholder="Example: \"Mam is not explaining concepts clearly in Data Structures\" or \"Bathroom in Main block is not clean\""
    )

    images_b64: List[str] = []
    if is_multimodal:
        files = st.file_uploader(
            "Attach image(s) if relevant",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True
        )
        if files:
            for f in files:
                enc = encode_image_to_base64(f)
                if enc:
                    images_b64.append(enc)

    # Additional context to guide LLM for edge cases
    st.expander("Advanced context (optional)").write(
        "Tips:\n"
        "- If hosteller and raises subtle facilities issues without building name, it should be Hostel.\n"
        "- If specific building (A, B, C, IT, ECE, Spark, CSE, Library, MBA, G, F) is mentioned, it should be Infrastructure.\n"
        "- Academic teaching/learning, labs, department staff → Academics.\n"
        "- If specifying a different department, route to that specified department."
    )

    # Confirm / Process
    colA, colB = st.columns([1,1])
    with colA:
        run_btn = st.button("Analyze and Rephrase", type="primary")
    with colB:
        reset_btn = st.button("Reset Form")

    if reset_btn:
        st.session_state.draft = None

    if run_btn:
        if not complaint_text and not images_b64:
            st.warning("Please enter a complaint or attach an image.")
            return

        # Fuse images if any into a single hint for LLM
        image_data = images_b64[0] if images_b64 else None

        # Build a profile context to help LLM resolve keywordless cases
        user_context = {
            "department": department,
            "gender": gender,
            "residence": residential,  # Hosteller or Day Scholar
        }

        # Call classifier (LLM-first classification)
        result = classifier.classify(
            complaint=complaint_text,
            user_department=department,
            upvotes=0,
            image_data=image_data
        )

        # Determine privacy and bypass visibility notes
        priv = privacy.determine_privacy(
            complaint=complaint_text,
            llm_result=result.detailed_analysis.get("classification", {})
        )

        # Rephrase complaint formally with fused signals
        rephrased = llm.rephrase_complaint(
            complaint_text,
            user_context=user_context,
            image_data=image_data,
            classification_hint=result.category
        )

        # Save draft to confirm later
        st.session_state.draft = {
            "raw_text": complaint_text,
            "images": images_b64,
            "model": cfg.current_model,
            "category": result.category,
            "final_authority": result.final_authority,
            "routing_path": result.routing_path,
            "priority_level": result.priority_level,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "used_image": result.used_image,
            "privacy": priv,
            "rephrased": rephrased,
            "detailed": result.detailed_analysis,
        }

    # Show draft and confirm submission
    if st.session_state.draft:
        d = st.session_state.draft
        st.subheader("AI Results")

        top_cols = st.columns(4)
        with top_cols[0]:
            st.markdown(as_badge(f"Category: {d['category'].title()}"), unsafe_allow_html=True)
        with top_cols[1]:
            st.markdown(as_badge(f"Priority: {d['priority_level']}"), unsafe_allow_html=True)
        with top_cols[2]:
            st.markdown(as_badge(f"Confidence: {d['confidence']}"), unsafe_allow_html=True)
        with top_cols[3]:
            st.markdown(as_badge("Image Used" if d["used_image"] else "Text Only"), unsafe_allow_html=True)

        st.markdown("#### Routing")
        st.info(f"Final Authority: {d['final_authority']}")
        show_routing_path(d["routing_path"])

        st.markdown("#### Privacy & Visibility")
        st.write(f"Privacy Level: {d['privacy']['privacy_level']}")
        st.write(f"Visibility: {d['privacy']['visibility']}")

        st.markdown("#### Formal Rephrasing (Confirm)")
        rephrased_text = st.text_area(
            "Review and edit if needed",
            value=d["rephrased"],
            height=140
        )

        confirm = st.button("Confirm and Submit")
        if confirm:
            item = {
                "final_text": rephrased_text.strip(),
                "category": d["category"],
                "final_authority": d["final_authority"],
                "routing_path": d["routing_path"],
                "privacy": d["privacy"],
                "priority": d["priority_level"],
                "model": d["model"],
                "used_image": d["used_image"]
            }
            st.session_state.submitted_items.append(item)
            st.success("Complaint submitted successfully.")
            st.session_state.draft = None

    if st.session_state.submitted_items:
        st.subheader("Recent Submissions")
        for i, it in enumerate(reversed(st.session_state.submitted_items[-5:]), 1):
            st.markdown(f"**#{i}. {it['category'].title()} → {it['final_authority']}**")
            st.markdown(f'<div class="small">Model: {it["model"]} • Priority: {it["priority"]} • Mode: {"Multimodal" if it["used_image"] else "Text"}</div>', unsafe_allow_html=True)
            show_routing_path(it["routing_path"])
            st.divider()

if __name__ == "__main__":
    main()
