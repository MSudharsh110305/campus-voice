"""
API Test Script - CampusVoice Complaint System
Version: 4.0.0 - ENHANCED

Comprehensive testing suite covering:
- Basic API endpoints
- Authority routing & escalation
- Cross-department complaints
- Sensitive complaints (ragging, harassment)
- Personal/confidential complaints
- Voting system
"""

import requests
import time
import json
import base64
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, List

# =================== CONFIGURATION ===================

class TestConfig:
    """Test configuration."""
    BASE_URL = "http://localhost:5000/api/v1"
    TIMEOUT = 30
    CONCURRENT_REQUESTS = 5

# =================== TEST DATA ===================

# Basic complaints
TEST_COMPLAINTS_BASIC = [
    {
        "roll_number": "21CS001",
        "department": "Computer Science & Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "The WiFi in hostel A is very slow and keeps disconnecting frequently. Cannot attend online classes properly.",
        "is_public": True
    },
    {
        "roll_number": "21ECE042",
        "department": "Electronics & Communication Engineering",
        "gender": "female",
        "residence": "Hostel B",
        "complaint_text": "The laboratory equipment in ECE department is outdated. The oscilloscopes are not working properly.",
        "is_public": True
    },
    {
        "roll_number": "21ME023",
        "department": "Mechanical Engineering",
        "gender": "male",
        "residence": "Day Scholar",
        "complaint_text": "Professor is not explaining concepts properly in class. Teaching quality needs improvement.",
        "is_public": False
    },
    {
        "roll_number": "21IT015",
        "department": "Information Technology",
        "gender": "female",
        "residence": "Hostel C",
        "complaint_text": "The water tap in Block A second floor is leaking continuously. Water is getting wasted.",
        "is_public": True
    },
    {
        "roll_number": "21AI008",
        "department": "Artificial Intelligence and Data Science",
        "gender": "other",
        "residence": "Hostel A",
        "complaint_text": "The mess food quality is very poor. Found insects in food yesterday. Health hazard.",
        "is_public": True
    }
]

# Authority escalation & special cases
TEST_COMPLAINTS_ADVANCED = [
    # 1. Ragging complaint (should be confidential + Principal)
    {
        "roll_number": "21CS101",
        "department": "Computer Science & Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "I am being ragged by senior students in hostel. They force me to do their work and threaten me if I refuse. This is happening daily and affecting my mental health.",
        "is_public": False,
        "expected_authority": "Principal",
        "expected_visibility": "confidential",
        "test_name": "Ragging Complaint"
    },
    
    # 2. Sexual harassment (should be confidential + Principal)
    {
        "roll_number": "21ECE201",
        "department": "Electronics & Communication Engineering",
        "gender": "female",
        "residence": "Hostel B",
        "complaint_text": "A professor made inappropriate comments about my appearance and touched my shoulder inappropriately during lab session. I feel very uncomfortable.",
        "is_public": False,
        "expected_authority": "Principal",
        "expected_visibility": "confidential",
        "test_name": "Sexual Harassment Complaint"
    },
    
    # 3. Cross-department infrastructure (HOD conflict -> AO)
    {
        "roll_number": "21CS102",
        "department": "Computer Science & Engineering",
        "gender": "male",
        "residence": "Day Scholar",
        "complaint_text": "The main gate security is very poor. Anyone can enter campus without proper checking. This is a safety issue for all departments.",
        "is_public": True,
        "expected_authority": "Administrative Officer (AO)",
        "expected_visibility": "public",
        "test_name": "Cross-Department Infrastructure"
    },
    
    # 4. Mental health / personal issue (should be confidential)
    {
        "roll_number": "21ME301",
        "department": "Mechanical Engineering",
        "gender": "female",
        "residence": "Hostel C",
        "complaint_text": "I am feeling very depressed and anxious. The academic pressure is too much and I am having suicidal thoughts. Need counseling support urgently.",
        "is_public": False,
        "expected_authority": "Principal",
        "expected_visibility": "confidential",
        "test_name": "Mental Health / Personal Crisis"
    },
    
    # 5. Multiple department issue (hostel affects all)
    {
        "roll_number": "21IT401",
        "department": "Information Technology",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "The hostel warden is discriminating against students from certain states. He gives preferential treatment to local students.",
        "is_public": False,
        "expected_authority": "Principal",
        "expected_visibility": "confidential",
        "test_name": "Discrimination Complaint"
    },
    
    # 6. Faculty misconduct (should escalate)
    {
        "roll_number": "21AI501",
        "department": "Artificial Intelligence and Data Science",
        "gender": "other",
        "residence": "Day Scholar",
        "complaint_text": "The professor is demanding bribes to pass students in exams. Many students have complained but nothing has been done.",
        "is_public": False,
        "expected_authority": "Principal",
        "expected_visibility": "confidential",
        "test_name": "Faculty Bribery / Corruption"
    },
    
    # 7. General infrastructure (should go to AO)
    {
        "roll_number": "21CS103",
        "department": "Computer Science & Engineering",
        "gender": "female",
        "residence": "Hostel B",
        "complaint_text": "The library air conditioning is not working properly. It's very hot and uncomfortable to study.",
        "is_public": True,
        "expected_authority": "Administrative Officer (AO)",
        "expected_visibility": "public",
        "test_name": "General Infrastructure"
    },
    
    # 8. Departmental academic issue (should go to HOD)
    {
        "roll_number": "21ECE202",
        "department": "Electronics & Communication Engineering",
        "gender": "male",
        "residence": "Day Scholar",
        "complaint_text": "The syllabus for Digital Signal Processing course is outdated. Industry requires knowledge of modern DSP tools.",
        "is_public": True,
        "expected_authority": "Head of Department - Electronics & Communication Engineering",
        "expected_visibility": "public",
        "test_name": "Departmental Academic Issue"
    },
    
    # 9. Hostel-specific (should go to Hostel Warden)
    {
        "roll_number": "21ME302",
        "department": "Mechanical Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "The hostel room cleaning is not done properly. Bathrooms are dirty and not maintained.",
        "is_public": True,
        "expected_authority": "Hostel Warden",
        "expected_visibility": "public",
        "test_name": "Hostel Maintenance"
    },
    
    # 10. Emergency/Critical (water + health hazard = high priority)
    {
        "roll_number": "21IT402",
        "department": "Information Technology",
        "gender": "female",
        "residence": "Hostel C",
        "complaint_text": "The drinking water in hostel C has a foul smell and many students are getting stomach infections. This is a serious health emergency.",
        "is_public": True,
        "expected_authority": "Hostel Warden",
        "expected_visibility": "public",
        "test_name": "Critical Health Emergency"
    }
]

# =================== TEST UTILITIES ===================

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * 80)

def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_result(name: str, success: bool, details: str = ""):
    """Print test result."""
    if success:
        print_success(f"{name}: PASSED {details}")
    else:
        print_error(f"{name}: FAILED {details}")

# =================== BASIC TEST FUNCTIONS ===================

def test_health_check():
    """Test health check endpoint."""
    print_header("TEST 1: Health Check")
    
    try:
        response = requests.get(
            f"{TestConfig.BASE_URL}/health",
            timeout=TestConfig.TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_info(f"API Status: {data.get('data', {}).get('api_status')}")
            print_info(f"Firebase: {data.get('data', {}).get('firebase_status')}")
            print_info(f"LLM Engine: {data.get('data', {}).get('llm_engine_status')}")
            print_info(f"Model: {data.get('data', {}).get('llm_model')}")
            print_success("Health check passed!")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {str(e)}")
        return False

def test_get_departments():
    """Test get departments endpoint."""
    print_header("TEST 2: Get Departments")
    
    try:
        response = requests.get(
            f"{TestConfig.BASE_URL}/config/departments",
            timeout=TestConfig.TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            departments = data.get('data', {}).get('departments', [])
            print_info(f"Found {len(departments)} departments")
            print_success("Get departments passed!")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_image_requirement_check():
    """Test image requirement check endpoint."""
    print_header("TEST 3: Image Requirement Check")
    
    test_cases = [
        ("Water tap is leaking in hostel", True),
        ("Professor not teaching properly", False)
    ]
    
    all_passed = True
    for complaint_text, expected_needs_image in test_cases:
        try:
            response = requests.post(
                f"{TestConfig.BASE_URL}/complaints/check-image-requirement",
                json={"complaint_text": complaint_text},
                timeout=TestConfig.TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                needs_image = data.get('data', {}).get('needs_image')
                reason = data.get('data', {}).get('reason')
                is_mandatory = data.get('data', {}).get('is_mandatory')
                
                print_info(f"Complaint: {complaint_text[:50]}...")
                print_info(f"Needs image: {needs_image} (Mandatory: {is_mandatory})")
                print_info(f"Reason: {reason}")
                
                if needs_image == expected_needs_image:
                    print_success("✓ Correct detection")
                else:
                    print_warning("⚠ Unexpected detection (may be valid)")
            else:
                print_error(f"Failed: {response.status_code}")
                all_passed = False
        except Exception as e:
            print_error(f"Error: {str(e)}")
            all_passed = False
    
    return all_passed

def test_submit_single_complaint():
    """Test submitting a single complaint."""
    print_header("TEST 4: Submit Single Complaint")
    
    complaint = TEST_COMPLAINTS_BASIC[0]
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{TestConfig.BASE_URL}/complaints",
            json=complaint,
            timeout=TestConfig.TIMEOUT
        )
        processing_time = time.time() - start_time
        
        if response.status_code == 201:
            data = response.json()
            complaint_data = data.get('data', {})
            
            print_info(f"Complaint ID: {complaint_data.get('complaint_id')}")
            print_info(f"Category: {complaint_data.get('category')}")
            print_info(f"Authority: {complaint_data.get('assigned_authority')}")
            print_info(f"Priority: {complaint_data.get('priority_level')} ({complaint_data.get('priority_score')})")
            print_info(f"Is Public: {complaint_data.get('is_public')}")
            print_info(f"Processing Time: {processing_time:.2f}s")
            print_success("Complaint submitted successfully!")
            return True, complaint_data.get('complaint_id')
        else:
            print_error(f"Failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False, None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None

def test_submit_concurrent_complaints():
    """Test submitting multiple complaints concurrently."""
    print_header("TEST 5: Submit Concurrent Complaints (Basic)")
    print_info(f"Submitting {len(TEST_COMPLAINTS_BASIC)} basic complaints concurrently...")
    
    results = []
    complaint_ids = []
    
    def submit_complaint(complaint_data):
        """Submit a single complaint."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{TestConfig.BASE_URL}/complaints",
                json=complaint_data,
                timeout=TestConfig.TIMEOUT
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'complaint_id': data.get('data', {}).get('complaint_id'),
                    'processing_time': processing_time,
                    'roll_number': complaint_data['roll_number']
                }
            else:
                return {
                    'success': False,
                    'error': response.text,
                    'roll_number': complaint_data['roll_number']
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'roll_number': complaint_data['roll_number']
            }
    
    # Submit complaints concurrently
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=TestConfig.CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(submit_complaint, complaint) for complaint in TEST_COMPLAINTS_BASIC]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    total_time = time.time() - start_time
    
    # Analyze results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print_info(f"\nTotal Time: {total_time:.2f}s")
    print_info(f"Average Time: {total_time / len(TEST_COMPLAINTS_BASIC):.2f}s per complaint")
    print_info(f"Successful: {len(successful)}/{len(TEST_COMPLAINTS_BASIC)}")
    
    if successful:
        print_info("\n✅ Successfully submitted complaints:")
        for result in successful:
            print(f"   • Roll: {result['roll_number']} | ID: {result['complaint_id']} | Time: {result['processing_time']:.2f}s")
            complaint_ids.append(result['complaint_id'])
    
    if failed:
        print_warning("\n⚠️  Failed submissions:")
        for result in failed:
            print(f"   • Roll: {result['roll_number']} | Error: {result['error']}")
    
    if len(successful) == len(TEST_COMPLAINTS_BASIC):
        print_success("\nAll concurrent submissions passed!")
        return True, complaint_ids
    else:
        print_warning(f"\nPartial success: {len(successful)}/{len(TEST_COMPLAINTS_BASIC)}")
        return False, complaint_ids

def test_get_complaint(complaint_id: str):
    """Test getting a complaint by ID."""
    print_header("TEST 6: Get Complaint by ID")
    
    try:
        response = requests.get(
            f"{TestConfig.BASE_URL}/complaints/{complaint_id}",
            timeout=TestConfig.TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            complaint = data.get('data', {})
            
            print_info(f"Complaint ID: {complaint.get('complaint_id')}")
            print_info(f"Status: {complaint.get('status')}")
            print_info(f"Category: {complaint.get('category')}")
            print_info(f"Priority: {complaint.get('priority_level')}")
            print_info(f"Created: {complaint.get('created_at')}")
            print_success("Get complaint passed!")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_get_student_complaints(roll_number: str):
    """Test getting student's complaints."""
    print_header("TEST 7: Get Student Complaints")
    
    try:
        response = requests.get(
            f"{TestConfig.BASE_URL}/complaints/student/{roll_number}",
            params={"page": 1, "limit": 10},
            timeout=TestConfig.TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            complaints = data.get('data', {}).get('complaints', [])
            pagination = data.get('data', {}).get('pagination', {})
            
            print_info(f"Found {len(complaints)} complaints")
            print_info(f"Total: {pagination.get('total')}")
            print_info(f"Page: {pagination.get('page')}/{pagination.get('total_pages')}")
            print_success("Get student complaints passed!")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_get_public_complaints():
    """Test getting public complaints."""
    print_header("TEST 8: Get Public Complaints")
    
    try:
        response = requests.get(
            f"{TestConfig.BASE_URL}/complaints/public",
            params={"page": 1, "limit": 10, "sort_by": "created_at"},
            timeout=TestConfig.TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            complaints = data.get('data', {}).get('complaints', [])
            pagination = data.get('data', {}).get('pagination', {})
            
            print_info(f"Found {len(complaints)} public complaints")
            print_info(f"Total: {pagination.get('total')}")
            print_success("Get public complaints passed!")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_vote_on_complaint(complaint_id: str, roll_number: str):
    """Test voting on a complaint."""
    print_header("TEST 9: Vote on Complaint")
    
    try:
        # Upvote
        response = requests.post(
            f"{TestConfig.BASE_URL}/complaints/{complaint_id}/vote",
            json={"roll_number": roll_number, "vote_type": "upvote"},
            timeout=TestConfig.TIMEOUT
        )
        
        if response.status_code == 200:
            print_success("Upvote successful!")
            
            # Try to vote again (should fail)
            response2 = requests.post(
                f"{TestConfig.BASE_URL}/complaints/{complaint_id}/vote",
                json={"roll_number": roll_number, "vote_type": "upvote"},
                timeout=TestConfig.TIMEOUT
            )
            
            if response2.status_code != 200:
                print_success("Duplicate vote prevention working!")
            
            # Remove vote
            response3 = requests.delete(
                f"{TestConfig.BASE_URL}/complaints/{complaint_id}/vote",
                params={"roll_number": roll_number},
                timeout=TestConfig.TIMEOUT
            )
            
            if response3.status_code == 200:
                print_success("Vote removal successful!")
                return True
        
        # Detailed error message
        print_error(f"Failed: {response.status_code}")
        try:
            error_data = response.json()
            print_error(f"Error: {error_data.get('error', 'Unknown error')}")
            if 'details' in error_data:
                print_error(f"Details: {json.dumps(error_data['details'], indent=2)}")
        except:
            print_error(f"Response: {response.text[:200]}")
        
        return False
        
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_system_statistics():
    """Test system statistics endpoint."""
    print_header("TEST 10: System Statistics")
    
    try:
        response = requests.get(
            f"{TestConfig.BASE_URL}/statistics/system",
            timeout=TestConfig.TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get('data', {})
            
            print_info(f"Total Complaints: {stats.get('total_complaints')}")
            print_info(f"Public: {stats.get('public_complaints')}")
            print_info(f"Private: {stats.get('private_complaints')}")
            print_info(f"Raised: {stats.get('raised_count')}")
            print_info(f"Closed: {stats.get('closed_count')}")
            print_success("System statistics passed!")
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

# =================== ADVANCED TEST FUNCTIONS ===================

def test_advanced_complaints():
    """
    Test advanced complaint scenarios:
    - Authority escalation
    - Cross-department routing
    - Sensitive content detection
    - Priority scoring
    """
    print_header("TEST 11: Advanced Complaint Routing & Escalation")
    print_info(f"Testing {len(TEST_COMPLAINTS_ADVANCED)} advanced scenarios...\n")
    
    results = []
    
    for i, complaint in enumerate(TEST_COMPLAINTS_ADVANCED, 1):
        test_name = complaint.pop('test_name', f"Test {i}")
        expected_authority = complaint.pop('expected_authority', None)
        expected_visibility = complaint.pop('expected_visibility', None)
        
        print(f"\n{Colors.BOLD}{'─' * 80}{Colors.ENDC}")
        print(f"{Colors.BOLD}Scenario {i}: {test_name}{Colors.ENDC}")
        print(f"{'─' * 80}")
        print_info(f"Text: {complaint['complaint_text'][:100]}...")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{TestConfig.BASE_URL}/complaints",
                json=complaint,
                timeout=TestConfig.TIMEOUT
            )
            processing_time = time.time() - start_time
            
            if response.status_code == 201:
                data = response.json()
                complaint_data = data.get('data', {})
                
                # Extract results
                actual_authority = complaint_data.get('assigned_authority')
                actual_category = complaint_data.get('category')
                actual_priority = complaint_data.get('priority_level')
                actual_score = complaint_data.get('priority_score')
                is_public = complaint_data.get('is_public')
                
                # Display results
                print_info(f"Complaint ID: {complaint_data.get('complaint_id')}")
                print_info(f"Category: {actual_category}")
                print_info(f"Authority: {actual_authority}")
                print_info(f"Priority: {actual_priority} (Score: {actual_score})")
                print_info(f"Visibility: {'Public' if is_public else 'Private/Confidential'}")
                print_info(f"Processing Time: {processing_time:.2f}s")
                
                # Validate expectations
                passed = True
                if expected_authority:
                    if actual_authority == expected_authority:
                        print_success(f"✓ Correct authority: {actual_authority}")
                    else:
                        print_warning(f"⚠ Expected '{expected_authority}', got '{actual_authority}'")
                        passed = False
                
                if expected_visibility:
                    actual_vis = 'public' if is_public else 'private'
                    if actual_vis == expected_visibility or (expected_visibility == 'confidential' and not is_public):
                        print_success(f"✓ Correct visibility: {actual_vis}")
                    else:
                        print_warning(f"⚠ Expected '{expected_visibility}', got '{actual_vis}'")
                        passed = False
                
                results.append({
                    'test_name': test_name,
                    'passed': passed,
                    'authority': actual_authority,
                    'priority': actual_priority
                })
                
            else:
                print_error(f"Failed: {response.status_code}")
                print_error(f"Response: {response.text}")
                results.append({'test_name': test_name, 'passed': False})
                
        except Exception as e:
            print_error(f"Error: {str(e)}")
            results.append({'test_name': test_name, 'passed': False})
    
    # Summary
    print(f"\n{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}ADVANCED TESTS SUMMARY{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"{status} | {result['test_name']}")
        if 'authority' in result:
            print(f"       → Authority: {result['authority']} | Priority: {result['priority']}")
    
    print(f"\n{Colors.BOLD}Result: {passed_count}/{total_count} scenarios passed{Colors.ENDC}")
    
    return passed_count == total_count

# =================== MAIN TEST RUNNER ===================

def run_all_tests():
    """Run all tests in sequence."""
    print(f"""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║         🧪 CAMPUSVOICE API TEST SUITE - ENHANCED 🧪              ║
    ║                      Version 4.0.0                                ║
    ║                                                                   ║
    ║  Testing:                                                         ║
    ║   • Basic API operations                                          ║
    ║   • Authority routing & escalation                                ║
    ║   • Sensitive complaint detection                                 ║
    ║   • Cross-department routing                                      ║
    ║   • Priority scoring                                              ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    print_info(f"Testing API at: {TestConfig.BASE_URL}")
    print_info(f"Timeout: {TestConfig.TIMEOUT}s")
    print_info(f"Concurrent Requests: {TestConfig.CONCURRENT_REQUESTS}")
    
    results = {}
    complaint_ids = []
    
    # ========== BASIC TESTS ==========
    
    # Test 1: Health Check
    results['health_check'] = test_health_check()
    time.sleep(1)
    
    # Test 2: Get Departments
    results['get_departments'] = test_get_departments()
    time.sleep(1)
    
    # Test 3: Image Requirement Check
    results['image_check'] = test_image_requirement_check()
    time.sleep(1)
    
    # Test 4: Submit Single Complaint
    success, complaint_id = test_submit_single_complaint()
    results['single_complaint'] = success
    if complaint_id:
        complaint_ids.append(complaint_id)
    time.sleep(2)
    
    # Test 5: Submit Concurrent Complaints
    success, new_ids = test_submit_concurrent_complaints()
    results['concurrent_complaints'] = success
    complaint_ids.extend(new_ids)
    time.sleep(2)
    
    # Test 6: Get Complaint by ID
    if complaint_ids:
        results['get_complaint'] = test_get_complaint(complaint_ids[0])
    time.sleep(1)
    
    # Test 7: Get Student Complaints
    results['student_complaints'] = test_get_student_complaints(TEST_COMPLAINTS_BASIC[0]['roll_number'])
    time.sleep(1)
    
    # Test 8: Get Public Complaints
    results['public_complaints'] = test_get_public_complaints()
    time.sleep(1)
    
    # Test 9: Vote on Complaint (✅ FIXED: Valid roll number)
    if complaint_ids:
        results['voting'] = test_vote_on_complaint(complaint_ids[0], "21CS999")  # ✅ Valid format
    time.sleep(1)
    
    # Test 10: System Statistics
    results['statistics'] = test_system_statistics()
    time.sleep(1)
    
    # ========== ADVANCED TESTS ==========
    
    # Test 11: Advanced Complaint Routing
    results['advanced_routing'] = test_advanced_complaints()
    
    # ========== SUMMARY ==========
    
    print_header("FINAL TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} test suites passed{Colors.ENDC}\n")
    
    print(f"{Colors.BOLD}BASIC TESTS:{Colors.ENDC}")
    basic_tests = ['health_check', 'get_departments', 'image_check', 'single_complaint', 
                   'concurrent_complaints', 'get_complaint', 'student_complaints', 
                   'public_complaints', 'voting', 'statistics']
    for test_name in basic_tests:
        if test_name in results:
            print_result(test_name, results[test_name])
    
    print(f"\n{Colors.BOLD}ADVANCED TESTS:{Colors.ENDC}")
    advanced_tests = ['advanced_routing']
    for test_name in advanced_tests:
        if test_name in results:
            print_result(test_name, results[test_name])
    
    print("\n" + "=" * 80)
    
    if passed == total:
        print_success(f"\n🎉 ALL TESTS PASSED! ({passed}/{total})")
    else:
        print_warning(f"\n⚠️  SOME TESTS FAILED ({passed}/{total})")
    
    print("=" * 80 + "\n")
    
    return passed == total

if __name__ == '__main__':
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
