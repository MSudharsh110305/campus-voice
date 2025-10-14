#!/usr/bin/env python3
import time
import json
import random
import string
import requests
from typing import Dict, Any, List, Tuple
from urllib.parse import urlencode

BASE_URL = "http://localhost:5000/api/v1"
TIMEOUT = 45
SLEEP_AFTER_POST = 1.5  # allow LLM/background processing to kick in

def api_url(path: str) -> str:
    return f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}"

def do_request(method: str, url: str, **kwargs) -> Tuple[int, Any]:
    try:
        resp = requests.request(method, url, timeout=TIMEOUT, **kwargs)
        try:
            return resp.status_code, resp.json()
        except Exception:
            return resp.status_code, resp.text
    except requests.exceptions.RequestException as e:
        return 0, {"error": str(e)}

def rnd_id(prefix="user"):
    return f"{prefix}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"

def assert_status(code: int, expected: List[int], context: str):
    ok = code in expected
    print(f"[{ 'PASS' if ok else 'FAIL' }] {context}: HTTP {code} expected {expected}")
    return ok

def pretty(x):
    return json.dumps(x, indent=2, ensure_ascii=False) if isinstance(x, (dict, list)) else str(x)

# Expanded, diverse complaints covering water, bathrooms, hostel food, facilities, classrooms,
# parking, roads, ground/playground, plus a few edge/adversarial cases.
COMPLAINT_FIXTURES = [
    # Drinking water: hostel and academic blocks
    {
        "complaint_text": "RO drinking water in Hostel A tastes saline and filters seem overdue; several students reported stomach upset.",
        "user_department": "Mechanical Engineering",
        "category_hint": "hostel",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "The water purifier near CSE block is not dispensing water; request urgent cartridge replacement.",
        "user_department": "Computer Science & Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },

    # Bathrooms and sanitation
    {
        "complaint_text": "Ground floor men’s bathroom in ECE building has broken taps and foul odor; housekeeping frequency is insufficient.",
        "user_department": "Electronics & Communication Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "Hostel B second floor common bathroom has clogged drains; water stagnation is creating mosquito problems.",
        "user_department": "Electrical & Electronics Engineering",
        "category_hint": "hostel",
        "visibility_expectation": "public_ok",
    },

    # Hostel food quality and hygiene
    {
        "complaint_text": "Hostel mess served undercooked chapati and improperly stored curd; request strict hygiene checks and menu rotation.",
        "user_department": "Biomedical Engineering",
        "category_hint": "hostel",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "Repeated reuse of oil in mess frying station causes smell and acidity; please replace oil and display change logs.",
        "user_department": "Information Technology",
        "category_hint": "hostel",
        "visibility_expectation": "public_ok",
    },

    # Other department facilities
    {
        "complaint_text": "Mechanical workshop lacks safety goggles and gloves; request PPE availability and safety briefing before lab sessions.",
        "user_department": "Mechanical Engineering",
        "category_hint": "academic",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "Civil department survey equipment (theodolites) are miscalibrated; practical readings are consistently off.",
        "user_department": "Civil Engineering",
        "category_hint": "academic",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "AI&DS lab GPUs are overbooked; need a booking system and clear per-student quotas to prevent misuse.",
        "user_department": "Artificial Intelligence and Data Science",
        "category_hint": "academic",
        "visibility_expectation": "public_ok",
    },

    # Classrooms: ventilation, projectors, seating
    {
        "complaint_text": "CS-203 classroom projector flickers and HDMI port is loose; classes are disrupted during presentations.",
        "user_department": "Computer Science & Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "Classroom IT-105 has poor ventilation and fans not working in the last two rows; students feel dizzy during afternoon sessions.",
        "user_department": "Information Technology",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },

    # Parking: congestion, safety
    {
        "complaint_text": "Two-wheeler parking near main gate is overcrowded; vehicles block emergency lane; request lane markings and security monitoring.",
        "user_department": "Robotics and Automation",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "Bicycle racks outside library are broken; cycles are falling and getting damaged.",
        "user_department": "Electronics & Instrumentation Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },

    # Roads and campus access
    {
        "complaint_text": "Potholes on the road between Mechanical block and Auditorium cause accidents during rain; request resurfacing.",
        "user_department": "Mechanical Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "Streetlights behind EIE block are non-functional; pathway is unsafe after 7 PM.",
        "user_department": "Electronics & Instrumentation Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },

    # Ground/playground and sports
    {
        "complaint_text": "Football ground grass is overgrown and boundary lines faded; injuries increased due to uneven surface.",
        "user_department": "Civil Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "Badminton court roof leaks during rain; wooden floor gets slippery and unsafe.",
        "user_department": "Management Studies",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },

    # Data privacy and sensitive governance
    {
        "complaint_text": "Notice board lists student phone numbers publicly; request masking or initials only to protect privacy.",
        "user_department": "Information Technology",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok_or_confidential",
    },

    # Sensitive: bribery or harassment (confidential)
    {
        "complaint_text": "A lab assistant informally asked for a payment to mark lab attendance; please handle this confidentially.",
        "user_department": "Electronics & Communication Engineering",
        "category_hint": "academic",
        "visibility_expectation": "confidential",
    },
    {
        "complaint_text": "Senior sends inappropriate messages to juniors after hours; request discreet action and counseling support.",
        "user_department": "Artificial Intelligence and Data Science",
        "category_hint": "hostel",
        "visibility_expectation": "confidential",
    },

    # Adversarial/noisy cases
    {
        "complaint_text": "Parking super bad pls fix ASAP!!!",
        "user_department": "Computer Science & Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },
    {
        "complaint_text": "Hostel A bathrooms dirty, very dirty, like daily dirty.",
        "user_department": "Biomedical Engineering",
        "category_hint": "hostel",
        "visibility_expectation": "public_ok",
    },

    # Duplicate case to test de-dup or clustering
    {
        "complaint_text": "Potholes on the road between Mechanical block and Auditorium cause accidents during rain; request resurfacing.",
        "user_department": "Mechanical Engineering",
        "category_hint": "infrastructure",
        "visibility_expectation": "public_ok",
    },
]

def submit_complaint(item, common_user):
    payload = {
        "complaint_text": item["complaint_text"],
        "user_id": common_user,
        "gender": random.choice(["male", "female", "other"]),
        "user_department": item["user_department"],
        "user_residence": random.choice(["Hostel A", "Hostel B", "Day Scholar"]),
    }
    code, data = do_request("POST", api_url("/complaints"), json=payload)
    ok = assert_status(code, [200, 201], "POST /complaints")
    if not ok:
        print(pretty(data))
    return code, data

def get_status(complaint_id):
    code, data = do_request("GET", api_url(f"/complaints/{complaint_id}/status"))
    assert_status(code, [200], f"GET /complaints/{complaint_id}/status")
    return code, data

def get_public(category=None, limit=20):
    params = {}
    if category:
        params["category"] = category
    params["limit"] = limit
    url = api_url("/complaints/public")
    if params:
        url = f"{url}?{urlencode(params)}"
    code, data = do_request("GET", url)
    assert_status(code, [200], "GET /complaints/public")
    return code, data

def vote(complaint_id, user_id, vote_type="upvote"):
    payload = {"user_id": user_id, "vote_type": vote_type}
    code, data = do_request("POST", api_url(f"/complaints/{complaint_id}/vote"), json=payload)
    assert_status(code, [200, 201], f"POST /complaints/{complaint_id}/vote")
    return code, data

def get_by_category(cat, department=None, limit=50):
    params = {"limit": limit}
    if department:
        params["department"] = department
    url = api_url(f"/complaints/categories/{cat}") + f"?{urlencode(params)}"
    code, data = do_request("GET", url)
    assert_status(code, [200], f"GET /complaints/categories/{cat}")
    return code, data

def health():
    code, data = do_request("GET", api_url("/health"))
    assert_status(code, [200], "GET /health")
    return code, data

def stats():
    code, data = do_request("GET", api_url("/stats"))
    assert_status(code, [200], "GET /stats")
    return code, data

def llm_capabilities():
    code, data = do_request("GET", api_url("/llm/capabilities"))
    assert_status(code, [200], "GET /llm/capabilities")
    return code, data

def departments():
    code, data = do_request("GET", api_url("/departments"))
    assert_status(code, [200], "GET /departments")
    return code, data

def main():
    print("=== Campus Grievance API Automated Test (Expanded) ===")
    print(f"Base: {BASE_URL}")

    # Basic system checks
    print("\n-- Health & Stats --")
    _ = health()
    _ = stats()
    _ = llm_capabilities()
    _ = departments()

    # Submit a batch of diverse complaints
    print("\n-- Submitting Complaints --")
    common_user = rnd_id("student")
    submitted: List[Dict[str, Any]] = []
    for item in COMPLAINT_FIXTURES:
        code, data = submit_complaint(item, common_user)
        submitted.append({"req": item, "resp": {"code": code, "data": data}})
        time.sleep(SLEEP_AFTER_POST)

    # Extract IDs that were created successfully
    created_ids = []
    for s in submitted:
        data = s["resp"]["data"]
        if isinstance(data, dict):
            for key in ["id", "complaint_id", "_id"]:
                if key in data:
                    created_ids.append(data[key])
                    break

    # Check status for created complaints
    print("\n-- Status Checks --")
    for cid in created_ids:
        code, data = get_status(cid)
        if isinstance(data, dict):
            llm_fields = ["visibility", "category", "routed_to", "priority", "rephrased_text"]
            missing = [f for f in llm_fields if f not in data]
            if missing:
                print(f"[WARN] {cid} missing fields: {missing}")
        time.sleep(0.5)

    # Fetch public lists
    print("\n-- Public Complaints --")
    _ = get_public(limit=50)
    for cat in ["hostel", "academic", "infrastructure"]:
        _ = get_public(category=cat, limit=25)

    # Vote on a couple of items if present
    print("\n-- Voting --")
    voter = rnd_id("tester")
    for cid in created_ids[:3]:
        vote(cid, voter, vote_type="upvote")
        time.sleep(0.3)
        vote(cid, voter, vote_type="downvote")

    # Category queries
    print("\n-- Category Browsing --")
    _ = get_by_category("hostel", limit=50)
    _ = get_by_category("academic", department="Computer Science & Engineering", limit=25)
    _ = get_by_category("infrastructure", limit=50)

    # Final stats
    print("\n-- Final Stats --")
    code, data = stats()
    print(pretty(data))

    # Summary
    print("\n=== Summary ===")
    print(f"Submitted: {len(submitted)}")
    print(f"Created IDs: {len(created_ids)}")
    print("IDs:", created_ids)

    # Dump verbose log to a file
    artifact = {
        "base_url": BASE_URL,
        "submitted": submitted,
        "created_ids": created_ids,
        "final_stats": data,
    }
    with open("test_results_campus_grievance.json", "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, ensure_ascii=False)
    print("Saved: test_results_campus_grievance.json")

if __name__ == "__main__":
    main()
