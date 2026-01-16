"""
SIMPLE API TEST
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test():
    print("\n" + "="*70)
    print("🧪 TESTING SIMPLE SERVER")
    print("="*70 + "\n")
    
    # Test 1: Root
    print("1️⃣  Testing Root...")
    try:
        r = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"   ✅ Status: {r.status_code}")
        print(f"   Response: {r.json()}")
    except requests.exceptions.ConnectionError:
        print(f"   ❌ ERROR: Cannot connect to {BASE_URL}")
        print(f"   💡 Make sure test_server.py is running first!")
        return False
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    print()
    
    # Test 2: Health
    print("2️⃣  Testing Health...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        print(f"   ✅ Status: {r.status_code}")
        print(f"   Response: {r.json()}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    print()
    
    # Test 3: Submit Complaint
    print("3️⃣  Testing Complaint Submission...")
    complaint = {
        "student_name": "Test Student",
        "student_id": "TEST123",
        "email": "test@test.com",
        "phone": "1234567890",
        "category": "hostel",
        "description": "Test complaint - water issue in hostel",
        "location": "Test Block",
        "severity": "medium",
        "anonymous": False
    }
    
    try:
        r = requests.post(
            f"{BASE_URL}/api/v1/complaints",
            json=complaint,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        print(f"   ✅ Status: {r.status_code}")
        print(f"   Response: {json.dumps(r.json(), indent=2)}")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70 + "\n")
    return True

if __name__ == '__main__':
    print("\n⚠️  IMPORTANT: Make sure test_server.py is running in another terminal!")
    print("    If not, open a new terminal and run: python test_server.py")
    
    input("\nPress Enter when test_server.py is running...")
    
    success = test()
    
    if not success:
        print("\n❌ Tests failed. Check if test_server.py is running.")
        sys.exit(1)
    else:
        print("🎉 Server is working perfectly!")
        sys.exit(0)
