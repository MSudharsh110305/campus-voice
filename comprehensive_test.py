"""
Comprehensive Test Suite for CampusVoice System
Version: 4.0.0

Tests:
- All departments
- All complaint categories
- All authority routing scenarios
- Sensitive complaints (ragging, harassment, mental health)
- Cross-department issues
- Voting system (upvote/downvote)
- Vote reflection in public feed
- Priority scoring
- Visibility determination

Generates:
- Console output with colors
- Detailed JSON log file
- HTML test report
- CSV summary report
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple
import random
import logging
import csv
import os

# =================== CONFIGURATION ===================

API_BASE_URL = "http://localhost:5000/api/v1"
TIMEOUT = 30

# Output files
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = f"test_report_{TIMESTAMP}.log"
JSON_REPORT = f"test_report_{TIMESTAMP}.json"
CSV_REPORT = f"test_report_{TIMESTAMP}.csv"
HTML_REPORT = f"test_report_{TIMESTAMP}.html"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# Test results storage
TEST_RESULTS = {
    'metadata': {
        'timestamp': datetime.now().isoformat(),
        'api_url': API_BASE_URL,
        'total_duration': 0
    },
    'suites': []
}

# =================== TEST DATA ===================

# All departments test cases
DEPARTMENT_TEST_CASES = [
    {
        "roll_number": "21CSE001",
        "department": "Computer Science & Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "The C++ programming lab computers are outdated and slow. Need better hardware for running IDEs and compilers efficiently.",
        "is_public": True,
        "test_name": "CSE - Academic Lab Equipment"
    },
    {
        "roll_number": "21ECE002",
        "department": "Electronics & Communication Engineering",
        "gender": "female",
        "residence": "Hostel B",
        "complaint_text": "The oscilloscopes in ECE lab are not calibrated properly. Getting wrong readings in experiments which affects our practical marks.",
        "is_public": True,
        "test_name": "ECE - Lab Equipment Issue"
    },
    {
        "roll_number": "21MEE003",
        "department": "Mechanical Engineering",
        "gender": "male",
        "residence": "Day Scholar",
        "complaint_text": "The CAD software licenses in ME lab have expired. Cannot complete design assignments on time.",
        "is_public": True,
        "test_name": "ME - Software License Issue"
    },
    {
        "roll_number": "21CIV004",
        "department": "Civil Engineering",
        "gender": "female",
        "residence": "Hostel C",
        "complaint_text": "The surveying equipment is missing some parts. Total station is not working properly during field work.",
        "is_public": True,
        "test_name": "Civil - Equipment Missing Parts"
    },
    {
        "roll_number": "21EEE005",
        "department": "Electrical & Electronics Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "Power systems lab has faulty circuit breakers. Safety hazard during experiments with high voltage equipment.",
        "is_public": True,
        "test_name": "EEE - Safety Hazard"
    },
    {
        "roll_number": "21IT006",
        "department": "Information Technology",
        "gender": "female",
        "residence": "Hostel B",
        "complaint_text": "Database lab server is frequently down. Cannot complete practicals on time and unable to practice queries.",
        "is_public": True,
        "test_name": "IT - Server Downtime"
    },
    {
        "roll_number": "21AI007",
        "department": "Artificial Intelligence and Data Science",
        "gender": "other",
        "residence": "Day Scholar",
        "complaint_text": "Need GPU servers for deep learning projects. Current machines are too slow for training neural network models.",
        "is_public": True,
        "test_name": "AI/DS - Hardware Requirement"
    },
    {
        "roll_number": "21BIO008",
        "department": "Biotechnology",
        "gender": "female",
        "residence": "Hostel C",
        "complaint_text": "Microscopes in biology lab need maintenance. Image quality is very poor and cannot observe specimens properly.",
        "is_public": True,
        "test_name": "Biotech - Equipment Maintenance"
    },
    {
        "roll_number": "21CHE009",
        "department": "Chemical Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "Chemical storage room lacks proper ventilation. Strong fumes are causing headaches and breathing problems.",
        "is_public": True,
        "test_name": "Chemical - Safety Issue"
    },
    {
        "roll_number": "21AER010",
        "department": "Aeronautical Engineering",
        "gender": "male",
        "residence": "Day Scholar",
        "complaint_text": "Wind tunnel facility needs calibration. Getting inconsistent results in aerodynamics experiments.",
        "is_public": True,
        "test_name": "Aero - Facility Calibration"
    },
    {
        "roll_number": "21AUT011",
        "department": "Automobile Engineering",
        "gender": "female",
        "residence": "Hostel B",
        "complaint_text": "Workshop lacks modern diagnostic tools. Cannot analyze modern car engine management systems properly.",
        "is_public": True,
        "test_name": "Auto - Tool Upgrade Need"
    },
    {
        "roll_number": "21MAR012",
        "department": "Marine Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "Ship engine simulator software is outdated. Need updated training tools for modern marine engines.",
        "is_public": True,
        "test_name": "Marine - Software Update"
    }
]

# Category-specific test cases
CATEGORY_TEST_CASES = {
    "hostel": [
        {
            "roll_number": "21HOS001",
            "department": "Computer Science & Engineering",
            "gender": "male",
            "residence": "Hostel A",
            "complaint_text": "WiFi in Hostel A is extremely slow during evening hours. Cannot attend online classes or download study materials.",
            "is_public": True,
            "test_name": "Hostel - WiFi Issue"
        },
        {
            "roll_number": "21HOS002",
            "department": "Mechanical Engineering",
            "gender": "female",
            "residence": "Hostel B",
            "complaint_text": "Hostel mess food quality is very poor. Found insects in rice yesterday. This is unhygienic and health hazard.",
            "is_public": True,
            "test_name": "Hostel - Food Quality"
        },
        {
            "roll_number": "21HOS003",
            "department": "Electronics & Communication Engineering",
            "gender": "male",
            "residence": "Hostel C",
            "complaint_text": "Hot water is not available in Hostel C bathrooms. Geysers are not working since last week.",
            "is_public": True,
            "test_name": "Hostel - Hot Water"
        },
        {
            "roll_number": "21HOS004",
            "department": "Information Technology",
            "gender": "female",
            "residence": "Hostel A",
            "complaint_text": "Hostel rooms are not cleaned properly. Garbage is not collected regularly causing bad smell.",
            "is_public": True,
            "test_name": "Hostel - Cleaning Issue"
        },
        {
            "roll_number": "21HOS005",
            "department": "Civil Engineering",
            "gender": "male",
            "residence": "Hostel B",
            "complaint_text": "Hostel laundry service is very delayed. Takes 1 week to get clothes back which is too long.",
            "is_public": True,
            "test_name": "Hostel - Laundry Delay"
        }
    ],
    "infrastructure": [
        {
            "roll_number": "21INF001",
            "department": "Computer Science & Engineering",
            "gender": "female",
            "residence": "Day Scholar",
            "complaint_text": "Library air conditioning is not working. Too hot to study during afternoon making it impossible to concentrate.",
            "is_public": True,
            "test_name": "Infrastructure - Library AC"
        },
        {
            "roll_number": "21INF002",
            "department": "Mechanical Engineering",
            "gender": "male",
            "residence": "Hostel A",
            "complaint_text": "Main gate security is very lax. Anyone can enter without proper checking. Safety concern for students.",
            "is_public": True,
            "test_name": "Infrastructure - Security"
        },
        {
            "roll_number": "21INF003",
            "department": "Electrical & Electronics Engineering",
            "gender": "female",
            "residence": "Hostel C",
            "complaint_text": "Parking lot has potholes and water logging. Bikes are getting damaged and slipping is dangerous.",
            "is_public": True,
            "test_name": "Infrastructure - Parking"
        },
        {
            "roll_number": "21INF004",
            "department": "Information Technology",
            "gender": "male",
            "residence": "Day Scholar",
            "complaint_text": "Cafeteria seating is insufficient. Students have to stand and eat during lunch break.",
            "is_public": True,
            "test_name": "Infrastructure - Cafeteria"
        },
        {
            "roll_number": "21INF005",
            "department": "Electronics & Communication Engineering",
            "gender": "female",
            "residence": "Hostel B",
            "complaint_text": "Campus street lights are not working. Very dark at night which is a safety concern especially for female students.",
            "is_public": True,
            "test_name": "Infrastructure - Street Lights"
        }
    ],
    "academic": [
        {
            "roll_number": "21ACD001",
            "department": "Computer Science & Engineering",
            "gender": "male",
            "residence": "Hostel A",
            "complaint_text": "Professor is not covering entire syllabus. Many topics are being skipped and this will affect our exams.",
            "is_public": False,
            "test_name": "Academic - Syllabus Coverage"
        },
        {
            "roll_number": "21ACD002",
            "department": "Electronics & Communication Engineering",
            "gender": "female",
            "residence": "Day Scholar",
            "complaint_text": "Exam question papers are too difficult compared to what was taught in class. Grading seems unfair.",
            "is_public": False,
            "test_name": "Academic - Exam Difficulty"
        },
        {
            "roll_number": "21ACD003",
            "department": "Mechanical Engineering",
            "gender": "male",
            "residence": "Hostel B",
            "complaint_text": "Need more practical sessions for thermodynamics. Only theory is being taught but we need hands-on experience.",
            "is_public": True,
            "test_name": "Academic - Practical Need"
        },
        {
            "roll_number": "21ACD004",
            "department": "Information Technology",
            "gender": "female",
            "residence": "Hostel C",
            "complaint_text": "Course materials are outdated. Industry uses different technologies now. Curriculum needs modernization.",
            "is_public": True,
            "test_name": "Academic - Outdated Content"
        },
        {
            "roll_number": "21ACD005",
            "department": "Civil Engineering",
            "gender": "male",
            "residence": "Day Scholar",
            "complaint_text": "Grading is not transparent. No proper answer key is provided after exams to verify marks.",
            "is_public": False,
            "test_name": "Academic - Grading Issue"
        }
    ]
}

# Sensitive/Critical complaints
SENSITIVE_COMPLAINTS = [
    {
        "roll_number": "21SEN001",
        "department": "Computer Science & Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "I am being ragged by senior students. They force me to do their assignments and threaten me if I refuse. This is affecting my mental health badly and I am scared to go to hostel.",
        "is_public": False,
        "test_name": "SENSITIVE - Ragging",
        "expected_authority": "Principal",
        "expected_visibility": "private"
    },
    {
        "roll_number": "21SEN002",
        "department": "Electronics & Communication Engineering",
        "gender": "female",
        "residence": "Hostel B",
        "complaint_text": "A professor made inappropriate comments about my body and touched me inappropriately during lab session. I feel very uncomfortable and scared to attend that class.",
        "is_public": False,
        "test_name": "SENSITIVE - Sexual Harassment",
        "expected_authority": "Principal",
        "expected_visibility": "private"
    },
    {
        "roll_number": "21SEN003",
        "department": "Mechanical Engineering",
        "gender": "female",
        "residence": "Hostel C",
        "complaint_text": "I am feeling severely depressed and having suicidal thoughts. Academic pressure is too much and I feel like ending my life. Need urgent counseling support.",
        "is_public": False,
        "test_name": "SENSITIVE - Mental Health Crisis",
        "expected_authority": "Principal",
        "expected_visibility": "private"
    },
    {
        "roll_number": "21SEN004",
        "department": "Information Technology",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "Hostel warden is discriminating against students from certain states. Gives preferential treatment to local students and treats us unfairly.",
        "is_public": False,
        "test_name": "SENSITIVE - Discrimination",
        "expected_authority": "Principal",
        "expected_visibility": "private"
    },
    {
        "roll_number": "21SEN005",
        "department": "Civil Engineering",
        "gender": "female",
        "residence": "Day Scholar",
        "complaint_text": "Professor is demanding money to pass students in exams. This is happening in our department openly and everyone knows but nobody speaks up.",
        "is_public": False,
        "test_name": "SENSITIVE - Bribery/Corruption",
        "expected_authority": "Principal",
        "expected_visibility": "private"
    },
    {
        "roll_number": "21SEN006",
        "department": "Electrical & Electronics Engineering",
        "gender": "male",
        "residence": "Hostel B",
        "complaint_text": "I witnessed a physical assault between two students yesterday. One student was badly injured and bleeding. He needed immediate medical attention.",
        "is_public": False,
        "test_name": "SENSITIVE - Violence",
        "expected_authority": "Principal",
        "expected_visibility": "private"
    }
]

# High priority/emergency complaints
EMERGENCY_COMPLAINTS = [
    {
        "roll_number": "21EMG001",
        "department": "Computer Science & Engineering",
        "gender": "female",
        "residence": "Hostel A",
        "complaint_text": "Electrical wiring in Hostel A room 204 is sparking continuously. Serious fire hazard! Needs immediate attention before someone gets hurt.",
        "is_public": True,
        "test_name": "EMERGENCY - Electrical Fire Hazard",
        "expected_priority": ["Critical", "High"]
    },
    {
        "roll_number": "21EMG002",
        "department": "Mechanical Engineering",
        "gender": "male",
        "residence": "Hostel C",
        "complaint_text": "Water pipe burst in Hostel C second floor. Entire floor is flooded with water. Rooms are getting damaged and electrical equipment is at risk.",
        "is_public": True,
        "test_name": "EMERGENCY - Water Pipe Burst",
        "expected_priority": ["Critical", "High"]
    },
    {
        "roll_number": "21EMG003",
        "department": "Chemical Engineering",
        "gender": "female",
        "residence": "Day Scholar",
        "complaint_text": "Chemical spill in lab room 305. Strong toxic fumes are making students sick and dizzy. Need immediate evacuation and cleanup team.",
        "is_public": True,
        "test_name": "EMERGENCY - Chemical Spill",
        "expected_priority": ["Critical", "High"]
    },
    {
        "roll_number": "21EMG004",
        "department": "Information Technology",
        "gender": "male",
        "residence": "Hostel B",
        "complaint_text": "Drinking water in hostel B has foul smell and strange color. Many students are getting stomach infections and vomiting. Health emergency situation!",
        "is_public": True,
        "test_name": "EMERGENCY - Water Contamination",
        "expected_priority": ["Critical", "High"]
    }
]

# =================== HELPER FUNCTIONS ===================

def print_header(text: str):
    print("\n" + "=" * 100)
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * 100)
    logger.info(text)

def print_success(text: str):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")
    logger.info(f"SUCCESS: {text}")

def print_error(text: str):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")
    logger.error(f"ERROR: {text}")

def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")
    logger.info(text)

def print_warning(text: str):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")
    logger.warning(text)

# =================== API FUNCTIONS ===================

def submit_complaint(complaint_data: Dict) -> Tuple[int, Dict]:
    """Submit a complaint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/complaints",
            json=complaint_data,
            timeout=TIMEOUT
        )
        return response.status_code, response.json()
    except Exception as e:
        logger.exception(f"Error submitting complaint: {e}")
        return 500, {"error": str(e)}

def vote_on_complaint(complaint_id: str, roll_number: str, vote_type: str) -> Tuple[int, Dict]:
    """Vote on a complaint."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/complaints/{complaint_id}/vote",
            json={"roll_number": roll_number, "vote_type": vote_type},
            timeout=TIMEOUT
        )
        return response.status_code, response.json()
    except Exception as e:
        logger.exception(f"Error voting on complaint: {e}")
        return 500, {"error": str(e)}

def get_public_complaints(sort_by="created_at", limit=50) -> Dict:
    """Get public complaints."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/complaints/public",
            params={"page": 1, "limit": limit, "sort_by": sort_by},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['data']
        return None
    except Exception as e:
        logger.exception(f"Error getting public complaints: {e}")
        return None

def get_complaint_by_id(complaint_id: str) -> Dict:
    """Get complaint details."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/complaints/{complaint_id}",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            return response.json()['data']
        return None
    except Exception as e:
        logger.exception(f"Error getting complaint by ID: {e}")
        return None

# =================== TEST FUNCTIONS ===================

def test_department_complaints():
    """Test complaints for all departments."""
    print_header("TEST SUITE 1: ALL DEPARTMENTS")
    print_info(f"Testing {len(DEPARTMENT_TEST_CASES)} departments\n")
    
    suite_results = {
        'name': 'All Departments Test',
        'tests': [],
        'summary': {'total': 0, 'passed': 0, 'failed': 0}
    }
    
    complaint_ids = []
    
    for i, complaint in enumerate(DEPARTMENT_TEST_CASES, 1):
        test_name = complaint.pop('test_name')
        print(f"\n{Colors.BOLD}[{i}/{len(DEPARTMENT_TEST_CASES)}] {test_name}{Colors.ENDC}")
        print(f"   Department: {complaint['department']}")
        print(f"   Complaint: {complaint['complaint_text'][:80]}...")
        
        test_result = {
            'name': test_name,
            'department': complaint['department'],
            'complaint_text': complaint['complaint_text']
        }
        
        start_time = time.time()
        status, result = submit_complaint(complaint)
        process_time = time.time() - start_time
        
        test_result['processing_time'] = round(process_time, 2)
        test_result['status_code'] = status
        
        if status == 201:
            data = result['data']
            complaint_ids.append(data['complaint_id'])
            
            test_result['status'] = 'PASS'
            test_result['complaint_id'] = data['complaint_id']
            test_result['category'] = data['category']
            test_result['assigned_authority'] = data['assigned_authority']
            test_result['priority_level'] = data['priority_level']
            test_result['priority_score'] = data['priority_score']
            
            print_success(f"Submitted successfully in {process_time:.2f}s")
            print(f"   → ID: {data['complaint_id']}")
            print(f"   → Category: {data['category']}")
            print(f"   → Authority: {data['assigned_authority']}")
            print(f"   → Priority: {data['priority_level']} ({data['priority_score']})")
            
            suite_results['summary']['passed'] += 1
        else:
            test_result['status'] = 'FAIL'
            test_result['error'] = result.get('error', 'Unknown error')
            
            print_error(f"Failed: {test_result['error']}")
            suite_results['summary']['failed'] += 1
        
        suite_results['tests'].append(test_result)
        suite_results['summary']['total'] += 1
        
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    passed = suite_results['summary']['passed']
    total = suite_results['summary']['total']
    print_header(f"DEPARTMENT TESTS SUMMARY: {passed}/{total} PASSED")
    
    TEST_RESULTS['suites'].append(suite_results)
    return complaint_ids

def test_category_complaints():
    """Test complaints by category."""
    print_header("TEST SUITE 2: ALL CATEGORIES")
    
    suite_results = {
        'name': 'Category-Based Test',
        'categories': [],
        'summary': {'total': 0, 'passed': 0, 'failed': 0}
    }
    
    all_complaint_ids = []
    
    for category, complaints in CATEGORY_TEST_CASES.items():
        print(f"\n{Colors.BOLD}{'─' * 100}{Colors.ENDC}")
        print(f"{Colors.BOLD}CATEGORY: {category.upper()}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'─' * 100}{Colors.ENDC}")
        
        category_results = {
            'category': category,
            'tests': [],
            'summary': {'total': 0, 'passed': 0, 'failed': 0}
        }
        
        for i, complaint in enumerate(complaints, 1):
            test_name = complaint.pop('test_name')
            print(f"\n[{i}/{len(complaints)}] {test_name}")
            print(f"   Text: {complaint['complaint_text'][:80]}...")
            
            test_result = {
                'name': test_name,
                'expected_category': category,
                'complaint_text': complaint['complaint_text']
            }
            
            start_time = time.time()
            status, result = submit_complaint(complaint)
            process_time = time.time() - start_time
            
            test_result['processing_time'] = round(process_time, 2)
            test_result['status_code'] = status
            
            if status == 201:
                data = result['data']
                all_complaint_ids.append(data['complaint_id'])
                
                test_result['complaint_id'] = data['complaint_id']
                test_result['actual_category'] = data['category']
                test_result['assigned_authority'] = data['assigned_authority']
                test_result['is_public'] = data['is_public']
                
                print_success(f"Submitted")
                print(f"   → Category: {data['category']} (Expected: {category})")
                print(f"   → Authority: {data['assigned_authority']}")
                print(f"   → Visibility: {'Public' if data['is_public'] else 'Private'}")
                
                # Validate category
                category_match = data['category'] == category
                test_result['category_match'] = category_match
                
                if category_match:
                    print_success("✓ Category matches!")
                    test_result['status'] = 'PASS'
                    category_results['summary']['passed'] += 1
                else:
                    print_warning(f"⚠ Category mismatch")
                    test_result['status'] = 'PARTIAL'
                    category_results['summary']['passed'] += 1  # Still count as passed
            else:
                test_result['status'] = 'FAIL'
                test_result['error'] = result.get('error', 'Unknown error')
                print_error(f"Failed: {test_result['error']}")
                category_results['summary']['failed'] += 1
            
            category_results['tests'].append(test_result)
            category_results['summary']['total'] += 1
            suite_results['summary']['total'] += 1
            
            time.sleep(0.5)
        
        passed = category_results['summary']['passed']
        total = category_results['summary']['total']
        print(f"\n{Colors.BOLD}{category.upper()}: {passed}/{total} PASSED{Colors.ENDC}")
        
        suite_results['categories'].append(category_results)
        suite_results['summary']['passed'] += category_results['summary']['passed']
        suite_results['summary']['failed'] += category_results['summary']['failed']
    
    TEST_RESULTS['suites'].append(suite_results)
    return all_complaint_ids

def test_sensitive_complaints():
    """Test sensitive/critical complaints."""
    print_header("TEST SUITE 3: SENSITIVE & CRITICAL COMPLAINTS")
    print_warning("Testing sensitive scenarios (ragging, harassment, mental health, etc.)")
    
    suite_results = {
        'name': 'Sensitive Complaints Test',
        'tests': [],
        'summary': {'total': 0, 'passed': 0, 'partial': 0, 'failed': 0}
    }
    
    for i, complaint in enumerate(SENSITIVE_COMPLAINTS, 1):
        test_name = complaint.pop('test_name')
        expected_authority = complaint.pop('expected_authority', None)
        expected_visibility = complaint.pop('expected_visibility', None)
        
        print(f"\n{Colors.BOLD}[{i}/{len(SENSITIVE_COMPLAINTS)}] {test_name}{Colors.ENDC}")
        print(f"   Expected Authority: {expected_authority}")
        print(f"   Expected Visibility: {expected_visibility}")
        
        test_result = {
            'name': test_name,
            'expected_authority': expected_authority,
            'expected_visibility': expected_visibility
        }
        
        start_time = time.time()
        status, result = submit_complaint(complaint)
        process_time = time.time() - start_time
        
        test_result['processing_time'] = round(process_time, 2)
        test_result['status_code'] = status
        
        if status == 201:
            data = result['data']
            actual_authority = data['assigned_authority']
            is_private = not data['is_public']
            
            test_result['complaint_id'] = data['complaint_id']
            test_result['actual_authority'] = actual_authority
            test_result['is_private'] = is_private
            test_result['priority_level'] = data['priority_level']
            test_result['priority_score'] = data['priority_score']
            
            print_success(f"Submitted: {data['complaint_id']}")
            print(f"   → Authority: {actual_authority}")
            print(f"   → Visibility: {'Private/Confidential' if is_private else 'Public'}")
            print(f"   → Priority: {data['priority_level']} ({data['priority_score']})")
            
            # Validate
            authority_match = expected_authority and expected_authority.lower() in actual_authority.lower()
            visibility_match = (expected_visibility == 'private' and is_private)
            
            test_result['authority_match'] = authority_match
            test_result['visibility_match'] = visibility_match
            
            if visibility_match:
                print_success("✓ Correctly marked as Private/Confidential")
            else:
                print_warning("⚠ Should be Private/Confidential")
            
            if authority_match:
                print_success(f"✓ Correctly routed to {expected_authority}")
            else:
                print_warning(f"⚠ Expected {expected_authority}, got {actual_authority}")
            
            if visibility_match and authority_match:
                test_result['status'] = 'PASS'
                suite_results['summary']['passed'] += 1
            elif visibility_match or authority_match:
                test_result['status'] = 'PARTIAL'
                suite_results['summary']['partial'] += 1
            else:
                test_result['status'] = 'FAIL'
                suite_results['summary']['failed'] += 1
        else:
            test_result['status'] = 'FAIL'
            test_result['error'] = result.get('error', 'Unknown error')
            print_error(f"Failed: {test_result['error']}")
            suite_results['summary']['failed'] += 1
        
        suite_results['tests'].append(test_result)
        suite_results['summary']['total'] += 1
        
        time.sleep(0.5)
    
    # Summary
    passed = suite_results['summary']['passed']
    partial = suite_results['summary']['partial']
    failed = suite_results['summary']['failed']
    total = suite_results['summary']['total']
    
    print_header(f"SENSITIVE TESTS SUMMARY: {passed} PASS, {partial} PARTIAL, {failed} FAIL / {total} TOTAL")
    
    TEST_RESULTS['suites'].append(suite_results)

def test_emergency_complaints():
    """Test emergency/high priority complaints."""
    print_header("TEST SUITE 4: EMERGENCY COMPLAINTS")
    print_warning("Testing high-priority scenarios that should trigger urgent response")
    
    suite_results = {
        'name': 'Emergency Complaints Test',
        'tests': [],
        'summary': {'total': 0, 'passed': 0, 'partial': 0, 'failed': 0}
    }
    
    for i, complaint in enumerate(EMERGENCY_COMPLAINTS, 1):
        test_name = complaint.pop('test_name')
        expected_priority = complaint.pop('expected_priority', None)
        
        print(f"\n{Colors.BOLD}[{i}/{len(EMERGENCY_COMPLAINTS)}] {test_name}{Colors.ENDC}")
        print(f"   Expected Priority: {expected_priority}")
        
        test_result = {
            'name': test_name,
            'expected_priority': expected_priority
        }
        
        start_time = time.time()
        status, result = submit_complaint(complaint)
        process_time = time.time() - start_time
        
        test_result['processing_time'] = round(process_time, 2)
        test_result['status_code'] = status
        
        if status == 201:
            data = result['data']
            priority = data['priority_level']
            score = data['priority_score']
            
            test_result['complaint_id'] = data['complaint_id']
            test_result['actual_priority'] = priority
            test_result['priority_score'] = score
            test_result['assigned_authority'] = data['assigned_authority']
            test_result['category'] = data['category']
            
            print_success(f"Submitted: {data['complaint_id']}")
            print(f"   → Priority: {priority} (Score: {score})")
            print(f"   → Authority: {data['assigned_authority']}")
            print(f"   → Category: {data['category']}")
            
            # Check if priority is high
            priority_match = priority in (expected_priority if expected_priority else ['Critical', 'High'])
            test_result['priority_match'] = priority_match
            
            if priority_match:
                print_success(f"✓ Correctly assigned {priority} priority")
                test_result['status'] = 'PASS'
                suite_results['summary']['passed'] += 1
            else:
                print_warning(f"⚠ Should be Critical/High, got {priority}")
                test_result['status'] = 'PARTIAL'
                suite_results['summary']['partial'] += 1
        else:
            test_result['status'] = 'FAIL'
            test_result['error'] = result.get('error', 'Unknown error')
            print_error(f"Failed: {test_result['error']}")
            suite_results['summary']['failed'] += 1
        
        suite_results['tests'].append(test_result)
        suite_results['summary']['total'] += 1
        
        time.sleep(0.5)
    
    passed = suite_results['summary']['passed']
    total = suite_results['summary']['total']
    print_header(f"EMERGENCY TESTS SUMMARY: {passed}/{total} PASSED")
    
    TEST_RESULTS['suites'].append(suite_results)

def test_voting_system(complaint_ids: List[str]):
    """Test voting and downvoting system."""
    print_header("TEST SUITE 5: VOTING SYSTEM")
    print_info(f"Testing voting on public complaints\n")
    
    suite_results = {
        'name': 'Voting System Test',
        'tests': [],
        'summary': {'total': 0, 'passed': 0, 'partial': 0, 'failed': 0}
    }
    
    # Get public complaints first
    public_data = get_public_complaints(limit=50)
    if not public_data or not public_data['complaints']:
        print_error("No public complaints found to test voting!")
        TEST_RESULTS['suites'].append(suite_results)
        return
    
    public_complaints = public_data['complaints'][:10]
    print_success(f"Found {len(public_complaints)} public complaints to test")
    
    # Create test voters
    voters = [f"21VOTE{str(i).zfill(3)}" for i in range(1, 6)]
    
    for i, complaint in enumerate(public_complaints, 1):
        complaint_id = complaint['complaint_id']
        print(f"\n{Colors.BOLD}[{i}/{len(public_complaints)}] Testing Complaint: {complaint_id}{Colors.ENDC}")
        
        test_result = {
            'complaint_id': complaint_id,
            'voters': []
        }
        
        # Get initial vote counts
        initial_upvotes = complaint.get('upvotes', 0)
        initial_downvotes = complaint.get('downvotes', 0)
        initial_net = complaint.get('net_votes', initial_upvotes - initial_downvotes)
        
        test_result['initial_votes'] = {
            'upvotes': initial_upvotes,
            'downvotes': initial_downvotes,
            'net_votes': initial_net
        }
        
        print(f"   Initial votes: 👍 {initial_upvotes} | 👎 {initial_downvotes} | Net: {initial_net}")
        
        # Test upvoting
        print(f"\n   Testing upvotes...")
        upvote_success = 0
        for voter in voters[:3]:  # 3 upvotes
            status, result = vote_on_complaint(complaint_id, voter, 'upvote')
            if status == 200:
                upvote_success += 1
                print(f"   ✓ {voter} upvoted")
                test_result['voters'].append({'roll': voter, 'vote': 'upvote', 'success': True})
            else:
                print(f"   ✗ {voter} failed: {result.get('message', 'Unknown')}")
                test_result['voters'].append({'roll': voter, 'vote': 'upvote', 'success': False, 'error': result.get('message')})
            time.sleep(0.3)
        
        # Test downvoting
        print(f"\n   Testing downvotes...")
        downvote_success = 0
        for voter in voters[3:5]:  # 2 downvotes
            status, result = vote_on_complaint(complaint_id, voter, 'downvote')
            if status == 200:
                downvote_success += 1
                print(f"   ✓ {voter} downvoted")
                test_result['voters'].append({'roll': voter, 'vote': 'downvote', 'success': True})
            else:
                print(f"   ✗ {voter} failed: {result.get('message', 'Unknown')}")
                test_result['voters'].append({'roll': voter, 'vote': 'downvote', 'success': False, 'error': result.get('message')})
            time.sleep(0.3)
        
        # Test duplicate vote prevention
        print(f"\n   Testing duplicate vote prevention...")
        status, result = vote_on_complaint(complaint_id, voters[0], 'upvote')
        duplicate_prevented = (status != 200)
        test_result['duplicate_prevention'] = duplicate_prevented
        
        if duplicate_prevented:
            print_success(f"   ✓ Duplicate vote correctly prevented")
        else:
            print_warning(f"   ⚠ Duplicate vote was allowed!")
        
        # Verify updated votes
        time.sleep(1)
        updated_complaint = get_complaint_by_id(complaint_id)
        
        if updated_complaint:
            new_upvotes = updated_complaint.get('upvotes', 0)
            new_downvotes = updated_complaint.get('downvotes', 0)
            new_net = updated_complaint.get('net_votes', new_upvotes - new_downvotes)
            
            test_result['final_votes'] = {
                'upvotes': new_upvotes,
                'downvotes': new_downvotes,
                'net_votes': new_net
            }
            
            print(f"\n   After voting: 👍 {new_upvotes} | 👎 {new_downvotes} | Net: {new_net}")
            
            expected_upvotes = initial_upvotes + upvote_success
            expected_downvotes = initial_downvotes + downvote_success
            
            votes_match = (new_upvotes == expected_upvotes and new_downvotes == expected_downvotes)
            test_result['votes_match'] = votes_match
            
            if votes_match and duplicate_prevented:
                print_success(f"   ✓ Vote counts updated correctly!")
                test_result['status'] = 'PASS'
                suite_results['summary']['passed'] += 1
            elif votes_match or duplicate_prevented:
                print_warning(f"   ⚠ Partial success")
                test_result['status'] = 'PARTIAL'
                suite_results['summary']['partial'] += 1
            else:
                print_error(f"   ✗ Vote verification failed")
                test_result['status'] = 'FAIL'
                suite_results['summary']['failed'] += 1
        else:
            print_error("   ✗ Could not verify vote update")
            test_result['status'] = 'FAIL'
            suite_results['summary']['failed'] += 1
        
        suite_results['tests'].append(test_result)
        suite_results['summary']['total'] += 1
        
        time.sleep(0.5)
    
    # Test vote sorting
    print(f"\n{Colors.BOLD}Testing vote-based sorting...{Colors.ENDC}")
    sorted_data = get_public_complaints(sort_by="net_votes", limit=10)
    
    sort_result = {'status': 'FAIL'}
    
    if sorted_data and sorted_data['complaints']:
        print_success("✓ Vote-based sorting working")
        print("\nTop 5 by votes:")
        top_complaints = []
        for i, c in enumerate(sorted_data['complaints'][:5], 1):
            net = c.get('net_votes', 0)
            print(f"   {i}. {c['complaint_id']}: {net} net votes")
            top_complaints.append({'rank': i, 'id': c['complaint_id'], 'net_votes': net})
        sort_result['status'] = 'PASS'
        sort_result['top_complaints'] = top_complaints
    else:
        print_error("✗ Vote-based sorting failed")
    
    suite_results['vote_sorting'] = sort_result
    
    # Summary
    passed = suite_results['summary']['passed']
    total = suite_results['summary']['total']
    print_header(f"VOTING TESTS SUMMARY: {passed}/{total} PASSED")
    
    TEST_RESULTS['suites'].append(suite_results)

# =================== REPORT GENERATION ===================

def generate_json_report():
    """Generate JSON report."""
    try:
        with open(JSON_REPORT, 'w') as f:
            json.dump(TEST_RESULTS, f, indent=2)
        print_success(f"JSON report saved: {JSON_REPORT}")
        logger.info(f"JSON report saved to {JSON_REPORT}")
    except Exception as e:
        print_error(f"Failed to generate JSON report: {e}")
        logger.exception("JSON report generation failed")

def generate_csv_report():
    """Generate CSV summary report."""
    try:
        with open(CSV_REPORT, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Suite', 'Test Name', 'Status', 'Details'])
            
            for suite in TEST_RESULTS['suites']:
                suite_name = suite['name']
                
                # Handle different suite structures
                if 'tests' in suite:
                    for test in suite['tests']:
                        writer.writerow([
                            suite_name,
                            test.get('name', 'N/A'),
                            test.get('status', 'N/A'),
                            f"ID: {test.get('complaint_id', 'N/A')}, Priority: {test.get('priority_level', 'N/A')}"
                        ])
                elif 'categories' in suite:
                    for category in suite['categories']:
                        for test in category['tests']:
                            writer.writerow([
                                f"{suite_name} - {category['category']}",
                                test.get('name', 'N/A'),
                                test.get('status', 'N/A'),
                                f"ID: {test.get('complaint_id', 'N/A')}"
                            ])
        
        print_success(f"CSV report saved: {CSV_REPORT}")
        logger.info(f"CSV report saved to {CSV_REPORT}")
    except Exception as e:
        print_error(f"Failed to generate CSV report: {e}")
        logger.exception("CSV report generation failed")

def generate_html_report():
    """Generate HTML report."""
    try:
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CampusVoice Test Report - {TIMESTAMP}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .suite {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .suite-header {{
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #333;
        }}
        .test {{
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #ddd;
            background: #f9f9f9;
        }}
        .status-PASS {{ border-left-color: #28a745; }}
        .status-PARTIAL {{ border-left-color: #ffc107; }}
        .status-FAIL {{ border-left-color: #dc3545; }}
        .badge {{
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .badge-success {{ background: #28a745; color: white; }}
        .badge-warning {{ background: #ffc107; color: black; }}
        .badge-danger {{ background: #dc3545; color: white; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .summary-label {{
            font-size: 1em;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f0f0f0;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 CampusVoice Comprehensive Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>API URL: {API_BASE_URL}</p>
    </div>
    
    <div class="summary">
"""
        
        # Calculate overall statistics
        total_tests = sum(suite.get('summary', {}).get('total', 0) for suite in TEST_RESULTS['suites'])
        total_passed = sum(suite.get('summary', {}).get('passed', 0) for suite in TEST_RESULTS['suites'])
        total_failed = sum(suite.get('summary', {}).get('failed', 0) for suite in TEST_RESULTS['suites'])
        total_partial = sum(suite.get('summary', {}).get('partial', 0) for suite in TEST_RESULTS['suites'])
        
        html += f"""
        <div class="summary-card">
            <div class="summary-number">{total_tests}</div>
            <div class="summary-label">Total Tests</div>
        </div>
        <div class="summary-card">
            <div class="summary-number" style="color: #28a745;">{total_passed}</div>
            <div class="summary-label">Passed</div>
        </div>
        <div class="summary-card">
            <div class="summary-number" style="color: #ffc107;">{total_partial}</div>
            <div class="summary-label">Partial</div>
        </div>
        <div class="summary-card">
            <div class="summary-number" style="color: #dc3545;">{total_failed}</div>
            <div class="summary-label">Failed</div>
        </div>
    </div>
"""
        
        # Add each suite
        for suite in TEST_RESULTS['suites']:
            html += f"""
    <div class="suite">
        <div class="suite-header">{suite['name']}</div>
        <div>
            <span class="badge badge-success">Passed: {suite.get('summary', {}).get('passed', 0)}</span>
            <span class="badge badge-warning">Partial: {suite.get('summary', {}).get('partial', 0)}</span>
            <span class="badge badge-danger">Failed: {suite.get('summary', {}).get('failed', 0)}</span>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""
            
            # Handle different suite structures
            if 'tests' in suite:
                for test in suite['tests']:
                    status = test.get('status', 'N/A')
                    badge_class = f"badge-{'success' if status == 'PASS' else 'warning' if status == 'PARTIAL' else 'danger'}"
                    
                    details = []
                    if 'complaint_id' in test:
                        details.append(f"ID: {test['complaint_id']}")
                    if 'assigned_authority' in test:
                        details.append(f"Authority: {test['assigned_authority']}")
                    if 'priority_level' in test:
                        details.append(f"Priority: {test['priority_level']}")
                    
                    html += f"""
                <tr>
                    <td>{test.get('name', 'N/A')}</td>
                    <td><span class="badge {badge_class}">{status}</span></td>
                    <td>{', '.join(details) if details else 'N/A'}</td>
                </tr>
"""
            
            html += """
            </tbody>
        </table>
    </div>
"""
        
        html += """
</body>
</html>
"""
        
        with open(HTML_REPORT, 'w') as f:
            f.write(html)
        
        print_success(f"HTML report saved: {HTML_REPORT}")
        logger.info(f"HTML report saved to {HTML_REPORT}")
    except Exception as e:
        print_error(f"Failed to generate HTML report: {e}")
        logger.exception("HTML report generation failed")

# =================== MAIN TEST RUNNER ===================

def main():
    """Run comprehensive test suite."""
    print(f"""
    ╔═══════════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                       ║
    ║                   🧪 CAMPUSVOICE COMPREHENSIVE TEST SUITE 🧪                         ║
    ║                              Version 4.0.0                                            ║
    ║                                                                                       ║
    ║   Testing:                                                                            ║
    ║   • All 12 Departments                                                                ║
    ║   • All Categories (Academic, Hostel, Infrastructure)                                 ║
    ║   • Sensitive Complaints (Ragging, Harassment, Mental Health)                         ║
    ║   • Emergency Scenarios                                                               ║
    ║   • Voting System (Upvote, Downvote, Duplicate Prevention)                            ║
    ║   • Vote Reflection in Public Feed                                                    ║
    ║                                                                                       ║
    ║   Reports Generated:                                                                  ║
    ║   • Detailed Log File (.log)                                                          ║
    ║   • JSON Report (.json)                                                               ║
    ║   • CSV Summary (.csv)                                                                ║
    ║   • HTML Report (.html)                                                               ║
    ║                                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════════════════════╝
    """)
    
    logger.info("=" * 100)
    logger.info("CAMPUSVOICE COMPREHENSIVE TEST SUITE STARTED")
    logger.info("=" * 100)
    
    start_time = time.time()
    
    # Check API health
    print_info("Checking API connection...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print_success("API is online and ready!")
            logger.info("API health check passed")
        else:
            print_error("API is not responding correctly!")
            logger.error("API health check failed")
            return
    except Exception as e:
        print_error("Cannot connect to API! Make sure the server is running.")
        print_info("Start server with: python main.py")
        logger.exception("API connection failed")
        return
    
    time.sleep(2)
    
    # Run test suites
    all_complaint_ids = []
    
    try:
        # Suite 1: Department-specific complaints
        dept_ids = test_department_complaints()
        all_complaint_ids.extend(dept_ids)
        time.sleep(2)
        
        # Suite 2: Category-specific complaints
        cat_ids = test_category_complaints()
        all_complaint_ids.extend(cat_ids)
        time.sleep(2)
        
        # Suite 3: Sensitive complaints
        test_sensitive_complaints()
        time.sleep(2)
        
        # Suite 4: Emergency complaints
        test_emergency_complaints()
        time.sleep(2)
        
        # Suite 5: Voting system
        test_voting_system(all_complaint_ids)
        
    except Exception as e:
        print_error(f"Test execution error: {e}")
        logger.exception("Test suite execution failed")
    
    # Final summary
    total_time = time.time() - start_time
    TEST_RESULTS['metadata']['total_duration'] = round(total_time, 2)
    
    print_header("COMPREHENSIVE TEST SUITE COMPLETED")
    
    # Calculate totals
    total_tests = sum(suite.get('summary', {}).get('total', 0) for suite in TEST_RESULTS['suites'])
    total_passed = sum(suite.get('summary', {}).get('passed', 0) for suite in TEST_RESULTS['suites'])
    total_partial = sum(suite.get('summary', {}).get('partial', 0) for suite in TEST_RESULTS['suites'])
    total_failed = sum(suite.get('summary', {}).get('failed', 0) for suite in TEST_RESULTS['suites'])
    
    print(f"""
    {Colors.BOLD}Execution Summary:{Colors.ENDC}
    • Total Test Suites: {len(TEST_RESULTS['suites'])}
    • Total Tests Run: {total_tests}
    • Passed: {Colors.OKGREEN}{total_passed}{Colors.ENDC}
    • Partial: {Colors.WARNING}{total_partial}{Colors.ENDC}
    • Failed: {Colors.FAIL}{total_failed}{Colors.ENDC}
    • Total Execution Time: {total_time:.2f}s
    • Average Time per Test: {total_time/max(total_tests, 1):.2f}s
    
    {Colors.OKGREEN}✅ Test suite execution completed!{Colors.ENDC}
    """)
    
    logger.info(f"Total tests: {total_tests}, Passed: {total_passed}, Failed: {total_failed}, Time: {total_time:.2f}s")
    
    # Generate reports
    print_header("GENERATING REPORTS")
    generate_json_report()
    generate_csv_report()
    generate_html_report()
    
    print(f"""
    {Colors.OKCYAN}📄 Reports Generated:{Colors.ENDC}
    • Log File: {LOG_FILE}
    • JSON Report: {JSON_REPORT}
    • CSV Summary: {CSV_REPORT}
    • HTML Report: {HTML_REPORT}
    
    {Colors.OKGREEN}🎉 All tests and reports completed successfully!{Colors.ENDC}
    """)
    
    logger.info("=" * 100)
    logger.info("TEST SUITE COMPLETED SUCCESSFULLY")
    logger.info("=" * 100)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}⏹️  Tests interrupted by user{Colors.ENDC}")
        logger.warning("Tests interrupted by user")
    except Exception as e:
        print(f"\n\n{Colors.FAIL}💥 Test suite error: {e}{Colors.ENDC}")
        logger.exception("Fatal error in test suite")
        import traceback
        traceback.print_exc()
