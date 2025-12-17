"""
Campus Voice API - Automated Endpoint Tester
Runs a suite of calls against http://localhost:8000/api/v1
and prints per-endpoint results + final summary.
"""

import requests
import json
import base64
import sys
from typing import Dict, Any, List, Optional, Tuple

# =================== CONFIGURATION ===================

BASE_URL = "http://localhost:8000/api/v1"
MAIN_URL = "http://localhost:8000"

print("=" * 70)
print("🎓 CAMPUS VOICE - API AUTOMATED TEST CLIENT")
print("=" * 70)
print(f"📡 API Base: {BASE_URL}")
print(f"🔗 Server: {MAIN_URL}")
print("=" * 70)
print()


def pretty_print_response(resp: requests.Response):
    """Pretty print API response"""
    print(f"\n{'━' * 70}")
    print(f"Status Code: {resp.status_code}")
    print(f"{'━' * 70}")
    try:
        data = resp.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except Exception:
        print(resp.text)
    print()


def test_connection() -> bool:
    """Quick check that the main server is up"""
    try:
        print("🔗 Testing connection to server root...")
        resp = requests.get(f"{MAIN_URL}/", timeout=5)
        if resp.status_code == 200:
            print("✅ Server root is running and responding!")
            try:
                j = resp.json()
                status = j.get("status", "<no status field>")
                print(f"   Root status: {status}")
            except Exception:
                print("   Root returned non‑JSON body.")
            return True
        else:
            print(f"⚠️ Server responded with status {resp.status_code}")
            pretty_print_response(resp)
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {MAIN_URL}")
        print("   Make sure Flask app (main.py) is running!")
        print("   Run: python main.py")
        return False
    except Exception as e:
        print(f"❌ Error during connection test: {e}")
        return False


# =================== TEST HELPERS ===================

class TestResult:
    def __init__(self, name: str, success: bool, details: str = ""):
        self.name = name
        self.success = success
        self.details = details


def assert_status_ok(resp: requests.Response, expected_codes: List[int]) -> Tuple[bool, str]:
    if resp.status_code in expected_codes:
        return True, f"Status {resp.status_code} in {expected_codes}"
    return False, f"Unexpected status {resp.status_code}, expected {expected_codes}"


# =================== INDIVIDUAL TESTS ===================

def test_health_main() -> TestResult:
    name = "GET /health (main)"
    print(f"\n▶ {name}")
    try:
        resp = requests.get(f"{MAIN_URL}/health", timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200])
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_health_api() -> TestResult:
    name = "GET /api/v1/health"
    print(f"\n▶ {name}")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200])
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_departments() -> TestResult:
    name = "GET /departments"
    print(f"\n▶ {name}")
    try:
        resp = requests.get(f"{BASE_URL}/departments", timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200])
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_llm_capabilities() -> TestResult:
    name = "GET /llm/capabilities"
    print(f"\n▶ {name}")
    try:
        resp = requests.get(f"{BASE_URL}/llm/capabilities", timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200])
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_post_complaint() -> Tuple[TestResult, Optional[str]]:
    """
    POST /complaints with a sample payload.
    Returns (TestResult, complaint_id or None)
    """
    name = "POST /complaints"
    print(f"\n▶ {name}")

    payload = {
        "complaint_text": "Automated test complaint about hostel food quality.",
        "user_id": "student_test_001",
        "gender": "male",
        "user_department": "Computer Science & Engineering",
        "user_residence": "Hostel A",
    }

    try:
        url = f"{BASE_URL}/complaints"
        print(f"📤 POST {url}")
        resp = requests.post(url, json=payload, timeout=10)
        pretty_print_response(resp)

        ok, msg = assert_status_ok(resp, [201])
        complaint_id = None
        if ok:
            try:
                data = resp.json()
                complaint_id = (
                    data.get("data", {}).get("complaint_id")
                    or data.get("complaint_id")
                )
                if complaint_id:
                    msg += f", complaint_id={complaint_id}"
                else:
                    msg += ", but no complaint_id found in response"
            except Exception as e:
                msg += f", JSON parse error: {e}"
        return TestResult(name, ok, msg), complaint_id
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}"), None


def test_check_image_requirement() -> TestResult:
    name = "POST /complaints/check-image-requirement"
    print(f"\n▶ {name}")

    payload = {
        "complaint_text": "There is water leakage near the restroom, photo might help."
    }

    try:
        url = f"{BASE_URL}/complaints/check-image-requirement"
        print(f"📤 POST {url}")
        resp = requests.post(url, json=payload, timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200, 400])
        # For test purposes, both 200 (valid) and 400 (too short / invalid) are acceptable
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_get_complaint_status(complaint_id: str) -> TestResult:
    name = f"GET /complaints/{complaint_id}/status"
    print(f"\n▶ {name}")
    try:
        url = f"{BASE_URL}/complaints/{complaint_id}/status"
        print(f"📥 GET {url}")
        resp = requests.get(url, timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200, 404])
        # For automated test, both 200 (found) and 404 (not yet processed) are acceptable
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_get_public_complaints() -> TestResult:
    name = "GET /complaints/public"
    print(f"\n▶ {name}")
    try:
        params = {"limit": "20"}
        url = f"{BASE_URL}/complaints/public"
        print(f"📥 GET {url}")
        print(f"   Params: {params}")
        resp = requests.get(url, params=params, timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200])
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_get_complaints_by_category(category: str = "hostel") -> TestResult:
    name = f"GET /complaints/categories/{category}"
    print(f"\n▶ {name}")
    try:
        params = {"limit": "20"}
        url = f"{BASE_URL}/complaints/categories/{category}"
        print(f"📥 GET {url}")
        print(f"   Params: {params}")
        resp = requests.get(url, params=params, timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200])
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_vote_on_complaint(complaint_id: Optional[str]) -> TestResult:
    """
    POST /complaints/<id>/vote
    If complaint_id is None, this test will be marked as skipped/fail with explanation.
    """
    if not complaint_id:
        return TestResult("POST /complaints/<id>/vote", False, "No complaint_id available to vote on")

    name = f"POST /complaints/{complaint_id}/vote"
    print(f"\n▶ {name}")
    try:
        url = f"{BASE_URL}/complaints/{complaint_id}/vote"
        payload = {"user_id": "user_test_001", "vote_type": "upvote"}
        print(f"📤 POST {url}")
        resp = requests.post(url, json=payload, timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200, 400])
        # 200 = vote recorded, 400 = validations (still endpoint alive)
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


def test_stats() -> TestResult:
    name = "GET /stats"
    print(f"\n▶ {name}")
    try:
        url = f"{BASE_URL}/stats"
        print(f"📥 GET {url}")
        resp = requests.get(url, timeout=10)
        pretty_print_response(resp)
        ok, msg = assert_status_ok(resp, [200])
        return TestResult(name, ok, msg)
    except Exception as e:
        return TestResult(name, False, f"Exception: {e}")


# =================== MAIN RUNNER ===================

def run_all_tests():
    if not test_connection():
        print("\n❌ Aborting test run: server not reachable.")
        sys.exit(1)

    results: List[TestResult] = []

    # 1. Health checks
    results.append(test_health_main())
    results.append(test_health_api())

    # 2. Basic info endpoints
    results.append(test_departments())
    results.append(test_llm_capabilities())

    # 3. Complaints workflow
    post_result, complaint_id = test_post_complaint()
    results.append(post_result)

    results.append(test_check_image_requirement())

    if complaint_id:
        results.append(test_get_complaint_status(complaint_id))
    else:
        results.append(TestResult("GET /complaints/<id>/status", False, "Skipped: no complaint_id from POST"))

    # 4. Public and category listing
    results.append(test_get_public_complaints())
    results.append(test_get_complaints_by_category("hostel"))

    # 5. Voting
    results.append(test_vote_on_complaint(complaint_id))

    # 6. Stats
    results.append(test_stats())

    # =================== SUMMARY ===================
    print("\n" + "=" * 70)
    print("📊 TEST RUN SUMMARY")
    print("=" * 70)

    passed = 0
    failed = 0
    for r in results:
        status = "PASS" if r.success else "FAIL"
        if r.success:
            passed += 1
        else:
            failed += 1
        print(f"- [{status}] {r.name} → {r.details}")

    print("=" * 70)
    print(f"✅ PASSED: {passed}")
    print(f"❌ FAILED: {failed}")
    if failed == 0:
        print("🎉 FINAL RESULT: ALL TESTS PASSED")
    else:
        print("⚠️ FINAL RESULT: SOME TESTS FAILED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
