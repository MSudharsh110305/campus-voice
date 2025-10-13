import streamlit as st
import requests
import json
from urllib.parse import urlencode

st.set_page_config(page_title="Campus Grievance API Tester", layout="wide")

# -------- Settings --------
st.sidebar.header("Settings")
base_url = st.sidebar.text_input("API Base URL", value="http://localhost:5000/api/v1")

def api_url(path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"

# Utility: do request safely
def do_request(method: str, url: str, **kwargs):
    try:
        resp = requests.request(method, url, timeout=30, **kwargs)
        try:
            data = resp.json()
        except Exception:
            data = resp.text
        return resp.status_code, data
    except requests.exceptions.RequestException as e:
        return 0, {"error": str(e)}

# Pretty JSON
def pretty(obj):
    if isinstance(obj, (dict, list)):
        return json.dumps(obj, indent=2, ensure_ascii=False)
    return str(obj)

st.title("Campus Grievance Portal - API Test Console")
st.caption("Submit complaints, check status, browse public items, vote, and view health/stats.")

# Tabs for endpoints
tabs = st.tabs([
    "Submit Complaint",
    "Status Lookup",
    "Public Complaints",
    "Vote",
    "By Category",
    "Health & Stats",
    "LLM Capabilities",
    "Departments",
])

# -------- Submit Complaint --------
with tabs[0]:
    st.subheader("Submit Pseudo-Anonymous Complaint")
    st.write("Only email is optional; no phone number is used.")

    col1, col2 = st.columns(2)
    with col1:
        complaint_text = st.text_area(
            "Complaint Text",
            height=180,
            placeholder="Describe the issue in detail...",
            value="The WiFi in hostel is extremely slow and disconnects frequently during online classes."
        )
        user_department = st.text_input(
            "Department (full name or abbreviation)",
            value="Computer Science & Engineering"
        )
        user_residence = st.text_input("Residence (optional)", value="Hostel A")
    with col2:
        user_email = st.text_input("Email (optional)", value="student@college.edu")
        image_b64 = st.text_area("Image (base64, optional)", height=120)
        submit_btn = st.button("Submit Complaint", use_container_width=True)

    if submit_btn:
        payload = {
            "complaint_text": complaint_text.strip(),
            "user_department": user_department.strip(),
        }
        if user_residence.strip():
            payload["user_residence"] = user_residence.strip()
        if user_email.strip():
            payload["user_email"] = user_email.strip()
        if image_b64.strip():
            payload["image_data"] = image_b64.strip()

        st.code(pretty(payload), language="json")
        code, data = do_request("POST", api_url("/complaints"), json=payload)
        st.write(f"Status: {code}")
        st.code(pretty(data), language="json")

# -------- Status Lookup --------
with tabs[1]:
    st.subheader("Lookup Complaint Status")
    complaint_id = st.text_input("Complaint ID", placeholder="complaint_1727xxxx_xxxx")
    if st.button("Get Status"):
        code, data = do_request("GET", api_url(f"/complaints/{complaint_id}/status"))
        st.write(f"Status: {code}")
        st.code(pretty(data), language="json")

# -------- Public Complaints --------
with tabs[2]:
    st.subheader("Browse Public Complaints")
    category = st.selectbox("Category filter", ["", "hostel", "academic", "infrastructure"], index=0)
    limit = st.slider("Limit", 1, 100, 20)
    params = {}
    if category:
        params["category"] = category
    params["limit"] = limit
    url = api_url("/complaints/public")
    if params:
        url = f"{url}?{urlencode(params)}"
    if st.button("Fetch Public Complaints"):
        code, data = do_request("GET", url)
        st.write(f"Status: {code}")
        st.code(pretty(data), language="json")

# -------- Vote --------
with tabs[3]:
    st.subheader("Vote on a Public Complaint")
    v_cid = st.text_input("Complaint ID to vote on")
    user_id = st.text_input("User ID", value="tester01")
    vote_type = st.selectbox("Vote Type", ["upvote", "downvote"], index=0)
    if st.button("Submit Vote"):
        payload = {"user_id": user_id.strip(), "vote_type": vote_type}
        code, data = do_request("POST", api_url(f"/complaints/{v_cid}/vote"), json=payload)
        st.write(f"Status: {code}")
        st.code(pretty(data), language="json")

# -------- By Category --------
with tabs[4]:
    st.subheader("Get Complaints by Category")
    cat = st.selectbox("Category", ["hostel", "academic", "infrastructure"], index=0)
    dept = st.text_input("Department (optional for academic)")
    limit2 = st.slider("Limit", 1, 100, 50, key="limit2")
    params = {"limit": limit2}
    if dept.strip():
        params["department"] = dept.strip()
    url = api_url(f"/complaints/categories/{cat}") + (f"?{urlencode(params)}" if params else "")
    if st.button("Fetch by Category"):
        code, data = do_request("GET", url)
        st.write(f"Status: {code}")
        st.code(pretty(data), language="json")

# -------- Health & Stats --------
with tabs[5]:
    st.subheader("Health & Stats")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Health Check"):
            code, data = do_request("GET", api_url("/health"))
            st.write(f"Status: {code}")
            st.code(pretty(data), language="json")
    with c2:
        if st.button("System Statistics"):
            code, data = do_request("GET", api_url("/stats"))
            st.write(f"Status: {code}")
            st.code(pretty(data), language="json")

# -------- LLM Capabilities --------
with tabs[6]:
    st.subheader("LLM Capabilities")
    if st.button("Get Capabilities"):
        code, data = do_request("GET", api_url("/llm/capabilities"))
        st.write(f"Status: {code}")
        st.code(pretty(data), language="json")

# -------- Departments --------
with tabs[7]:
    st.subheader("Departments")
    if st.button("Get Departments"):
        code, data = do_request("GET", api_url("/departments"))
        st.write(f"Status: {code}")
        st.code(pretty(data), language="json")
