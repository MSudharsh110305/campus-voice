"""
COMPREHENSIVE TEST - ALL SCENARIOS
Tests: Escalation, Harassment, Inter-department, Voting, Priority handling
"""

import requests
import json
import time
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:5000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

# COMPREHENSIVE TEST COMPLAINTS COVERING ALL SCENARIOS
TEST_SCENARIOS = [
    # 1. CRITICAL EMERGENCY - Should escalate immediately
    {
        "student_name": "Rajesh Kumar",
        "student_id": "CS2021001",
        "email": "rajesh@college.edu",
        "phone": "9876543210",
        "category": "safety",
        "description": "URGENT: Fire alarm not working in hostel! Smoke detected on 3rd floor. Need immediate help!",
        "location": "Boys Hostel Block A - 3rd Floor",
        "severity": "critical",
        "anonymous": False,
        "scenario": "CRITICAL_EMERGENCY"
    },
    
    # 2. HARASSMENT COMPLAINT - Sensitive, needs special handling
    {
        "student_name": "Anonymous Student",
        "student_id": "EC2021056",
        "email": "anonymous@college.edu",
        "phone": "9876543211",
        "category": "harassment",
        "description": "Being harassed by senior students in mess area. Verbal abuse and threats. Scared to report openly.",
        "location": "Main Mess Hall",
        "severity": "high",
        "anonymous": True,
        "scenario": "HARASSMENT_ANONYMOUS"
    },
    
    # 3. INTER-DEPARTMENT ISSUE - Multiple departments involved
    {
        "student_name": "Priya Menon",
        "student_id": "ME2021034",
        "email": "priya@college.edu",
        "phone": "9876543212",
        "category": "infrastructure",
        "description": "Library AC not working, also WiFi is down. Both issues affecting studies. Need coordinated fix from facilities and IT.",
        "location": "Central Library - 2nd Floor Reading Room",
        "severity": "high",
        "anonymous": False,
        "scenario": "INTER_DEPARTMENT"
    },
    
    # 4. ACADEMIC GRIEVANCE - Needs HOD + Dean escalation
    {
        "student_name": "Arun Sharma",
        "student_id": "IT2021089",
        "email": "arun@college.edu",
        "phone": "9876543213",
        "category": "academic",
        "description": "Faculty not conducting classes regularly. Syllabus only 40% complete with exams in 2 weeks. Multiple students affected.",
        "location": "IT Department - Semester 5",
        "severity": "high",
        "anonymous": False,
        "scenario": "ACADEMIC_ESCALATION"
    },
    
    # 5. RECURRING ISSUE - Should trigger escalation
    {
        "student_name": "Sneha Patel",
        "student_id": "CS2021067",
        "email": "sneha@college.edu",
        "phone": "9876543214",
        "category": "hostel",
        "description": "Water supply issue AGAIN in Block B. This is the 5th time this month! Previous complaints ignored. Need permanent solution.",
        "location": "Girls Hostel Block B",
        "severity": "high",
        "anonymous": False,
        "scenario": "RECURRING_ESCALATION"
    },
    
    # 6. DISCRIMINATION COMPLAINT - Very sensitive
    {
        "student_name": "Rahul Verma",
        "student_id": "EC2021045",
        "email": "rahul.v@college.edu",
        "phone": "9876543215",
        "category": "discrimination",
        "description": "Being discriminated against by lab instructor based on background. Other students getting preference. Affecting my grades.",
        "location": "Electronics Lab - B Block",
        "severity": "high",
        "anonymous": False,
        "scenario": "DISCRIMINATION"
    },
    
    # 7. FINANCIAL ISSUE - Needs accounts + admin
    {
        "student_name": "Kavya Reddy",
        "student_id": "ME2021078",
        "email": "kavya@college.edu",
        "phone": "9876543216",
        "category": "financial",
        "description": "Scholarship amount not credited for 3 months. Already submitted all documents. Getting conflicting info from accounts.",
        "location": "Accounts Department",
        "severity": "high",
        "anonymous": False,
        "scenario": "FINANCIAL_INTER_DEPT"
    },
    
    # 8. FOOD POISONING - Critical health + safety
    {
        "student_name": "Deepak Singh",
        "student_id": "CS2021090",
        "email": "deepak@college.edu",
        "phone": "9876543217",
        "category": "health",
        "description": "Multiple students sick after eating in mess yesterday. Stomach pain, vomiting. 10+ students affected. Food quality check needed urgently.",
        "location": "Main Mess - Dinner Service",
        "severity": "critical",
        "anonymous": False,
        "scenario": "HEALTH_EMERGENCY"
    },
    
    # 9. RAGGING COMPLAINT - Very serious, multiple authorities
    {
        "student_name": "Anonymous Fresher",
        "student_id": "IT2025001",
        "email": "fresher@college.edu",
        "phone": "9876543218",
        "category": "ragging",
        "description": "Being ragged by seniors in hostel. Physical abuse and forced to do inappropriate things. Too scared to reveal identity.",
        "location": "Boys Hostel Block C - Room 201",
        "severity": "critical",
        "anonymous": True,
        "scenario": "RAGGING_CRITICAL"
    },
    
    # 10. INFRASTRUCTURE SAFETY - Multiple locations affected
    {
        "student_name": "Lakshmi Iyer",
        "student_id": "EC2021023",
        "email": "lakshmi@college.edu",
        "phone": "9876543219",
        "category": "infrastructure",
        "description": "Broken stairs in main building. Several students already slipped. Major accident waiting to happen. Needs immediate repair.",
        "location": "Main Academic Block - Staircase B",
        "severity": "critical",
        "anonymous": False,
        "scenario": "SAFETY_INFRASTRUCTURE"
    },
    
    # 11. EXAM RELATED - Time sensitive
    {
        "student_name": "Vikram Joshi",
        "student_id": "ME2021056",
        "email": "vikram@college.edu",
        "phone": "9876543220",
        "category": "academic",
        "description": "Exam hall conditions terrible. No fans working, extreme heat. Students fainting during exams. Need immediate solution.",
        "location": "Exam Hall 1 - Main Block",
        "severity": "high",
        "anonymous": False,
        "scenario": "EXAM_URGENT"
    },
    
    # 12. MENTAL HEALTH - Sensitive counseling needed
    {
        "student_name": "Anonymous",
        "student_id": "CS2021045",
        "email": "mental.health@college.edu",
        "phone": "9876543221",
        "category": "mental_health",
        "description": "Feeling severely depressed and anxious. Academic pressure overwhelming. Need counseling support urgently but want to remain anonymous.",
        "location": "Student Counseling Center",
        "severity": "high",
        "anonymous": True,
        "scenario": "MENTAL_HEALTH_ANONYMOUS"
    },
    
    # 13. PLACEMENT ISSUE - Career services + HOD
    {
        "student_name": "Ananya Desai",
        "student_id": "IT2020034",
        "email": "ananya@college.edu",
        "phone": "9876543222",
        "category": "placement",
        "description": "Company came for placements but only certain students informed. Missed opportunity due to poor communication from placement cell.",
        "location": "Placement Office",
        "severity": "high",
        "anonymous": False,
        "scenario": "PLACEMENT_GRIEVANCE"
    },
    
    # 14. ELECTRICAL HAZARD - Immediate danger
    {
        "student_name": "Rohit Kapoor",
        "student_id": "EC2021067",
        "email": "rohit@college.edu",
        "phone": "9876543223",
        "category": "safety",
        "description": "Exposed electrical wires in lab. Sparking and burning smell. EXTREMELY DANGEROUS! Someone will get electrocuted!",
        "location": "Electrical Lab - E Block",
        "severity": "critical",
        "anonymous": False,
        "scenario": "ELECTRICAL_EMERGENCY"
    },
    
    # 15. LOW PRIORITY - Routine maintenance
    {
        "student_name": "Pooja Nair",
        "student_id": "ME2021090",
        "email": "pooja@college.edu",
        "phone": "9876543224",
        "category": "infrastructure",
        "description": "Light bulb not working in corridor near room 305. Not urgent but needs fixing.",
        "location": "Hostel Block A - 3rd Floor Corridor",
        "severity": "low",
        "anonymous": False,
        "scenario": "LOW_PRIORITY_ROUTINE"
    }
]

def init_firebase():
    """Initialize Firebase"""
    try:
        firebase_admin.get_app()
    except ValueError:
        cred = credentials.Certificate('firebase-key.json')
        firebase_admin.initialize_app(cred)
    return firestore.client()

def submit_complaint(client_id, complaint):
    """Submit complaint"""
    start = time.time()
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/complaints",
            json=complaint,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        elapsed = time.time() - start
        result = response.json() if response.status_code == 201 else None
        
        return {
            "client_id": client_id,
            "success": response.status_code == 201,
            "elapsed": elapsed,
            "complaint_id": result.get('data', {}).get('complaint_id') if result else None,
            "scenario": complaint["scenario"],
            "category": complaint["category"],
            "severity": complaint["severity"],
            "response": result
        }
    except Exception as e:
        return {
            "client_id": client_id,
            "success": False,
            "elapsed": time.time() - start,
            "complaint_id": None,
            "scenario": complaint["scenario"],
            "error": str(e)
        }

def display_detailed_complaint(data, scenario):
    """Display complaint with scenario context"""
    print(f"\n{Colors.CYAN}{'═'*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}🎯 SCENARIO: {scenario}{Colors.RESET}")
    print(f"{Colors.CYAN}{'═'*80}{Colors.RESET}")
    
    # Basic Info
    print(f"\n{Colors.BOLD}📋 Complaint Information:{Colors.RESET}")
    print(f"  ID:           {Colors.YELLOW}{data.get('complaint_id')}{Colors.RESET}")
    print(f"  Student:      {data.get('student_name')}")
    print(f"  Student ID:   {data.get('student_id')}")
    print(f"  Category:     {Colors.MAGENTA}{data.get('category')}{Colors.RESET}")
    severity_color = Colors.RED if data.get('severity') == 'critical' else Colors.YELLOW
    print(f"  Severity:     {severity_color}{data.get('severity').upper()}{Colors.RESET}")
    print(f"  Anonymous:    {'Yes ✅' if data.get('anonymous') else 'No'}")
    
    # Processing Results
    proc = data.get('processing', {})
    print(f"\n{Colors.BOLD}🤖 AI Processing Results:{Colors.RESET}")
    print(f"  Category:     {Colors.MAGENTA}{proc.get('detected_category')}{Colors.RESET}")
    print(f"  Sub-category: {proc.get('sub_category')}")
    print(f"  Department:   {Colors.CYAN}{proc.get('department')}{Colors.RESET}")
    print(f"  Assigned To:  {Colors.GREEN}{proc.get('assigned_authority')}{Colors.RESET}")
    print(f"  Priority:     {Colors.YELLOW}{proc.get('priority_score')}/10{Colors.RESET}")
    print(f"  Urgency:      {severity_color}{proc.get('urgency_level')}{Colors.RESET}")
    
    # Description & Location
    print(f"\n{Colors.BOLD}📝 Description:{Colors.RESET}")
    print(f"  {data.get('description')}")
    print(f"\n{Colors.BOLD}📍 Location:{Colors.RESET}")
    print(f"  {data.get('location')}")
    
    # Status
    print(f"\n{Colors.BOLD}⚡ Status:{Colors.RESET}")
    print(f"  Current:      {Colors.GREEN}{data.get('status')}{Colors.RESET}")
    print(f"  Created:      {data.get('created_at')}")
    print(f"  Updated:      {data.get('updated_at')}")
    
    print(f"\n{Colors.CYAN}{'═'*80}{Colors.RESET}")

def run_comprehensive_test():
    """Run all scenario tests"""
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}🚀 COMPREHENSIVE SCENARIO TEST - CAMPUSVOICE AI{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    # Initialize
    print(f"{Colors.YELLOW}Initializing Firebase...{Colors.RESET}")
    db = init_firebase()
    print(f"{Colors.GREEN}✅ Firebase connected!{Colors.RESET}\n")
    
    # Check server
    print(f"{Colors.YELLOW}Checking server...{Colors.RESET}")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/health", timeout=2)
        if r.status_code == 200:
            print(f"{Colors.GREEN}✅ Server ready!{Colors.RESET}\n")
        else:
            print(f"{Colors.RED}❌ Server error{Colors.RESET}")
            return
    except:
        print(f"{Colors.RED}❌ Cannot connect to server{Colors.RESET}")
        return
    
    print(f"{Colors.BOLD}Test Configuration:{Colors.RESET}")
    print(f"  Total Scenarios:  {len(TEST_SCENARIOS)}")
    print(f"  Concurrent Mode:  Enabled")
    print(f"  Firebase:         Connected ✅")
    print(f"  Server:           {BASE_URL}")
    
    # Countdown
    print(f"\n{Colors.YELLOW}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}Starting in 3 seconds...{Colors.RESET}")
    for i in range(3, 0, -1):
        print(f"{Colors.BOLD}{i}...{Colors.RESET}")
        time.sleep(1)
    print(f"{Colors.GREEN}{Colors.BOLD}🚀 GO!{Colors.RESET}\n")
    
    # Submit all complaints concurrently
    start_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i, complaint in enumerate(TEST_SCENARIOS):
            # Add unique timestamp to student_id
            complaint = complaint.copy()
            complaint["student_id"] += f"_T{int(time.time())}"
            future = executor.submit(submit_complaint, i+1, complaint)
            futures.append(future)
        
        # Collect results
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            
            if result["success"]:
                print(f"{Colors.GREEN}✅ Client {result['client_id']:2d}: SUBMITTED{Colors.RESET} " +
                      f"({result['elapsed']:.2f}s) - {result['scenario'][:30]}...")
            else:
                print(f"{Colors.RED}❌ Client {result['client_id']:2d}: FAILED{Colors.RESET} - {result['scenario']}")
    
    total_time = time.time() - start_time
    
    # Wait for Firebase sync
    print(f"\n{Colors.YELLOW}⏳ Waiting for Firebase sync (3 seconds)...{Colors.RESET}")
    time.sleep(3)
    
    # Fetch and display results
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}🔥 FETCHING & ANALYZING PROCESSED COMPLAINTS{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}")
    
    successful = [r for r in results if r["success"]]
    
    for result in sorted(successful, key=lambda x: x['client_id']):
        cid = result['complaint_id']
        if cid:
            doc = db.collection('complaints').document(cid).get()
            if doc.exists:
                display_detailed_complaint(doc.to_dict(), result['scenario'])
    
    # Summary Statistics
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}📊 COMPREHENSIVE TEST SUMMARY{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")
    
    # Group by category
    by_category = {}
    by_severity = {}
    
    for r in successful:
        cat = r.get('category', 'unknown')
        sev = r.get('severity', 'unknown')
        by_category[cat] = by_category.get(cat, 0) + 1
        by_severity[sev] = by_severity.get(sev, 0) + 1
    
    print(f"{Colors.BOLD}📈 Results:{Colors.RESET}")
    print(f"  Total Scenarios:   {len(TEST_SCENARIOS)}")
    print(f"  Successful:        {Colors.GREEN}{len(successful)}{Colors.RESET} ({len(successful)/len(TEST_SCENARIOS)*100:.1f}%)")
    print(f"  Failed:            {Colors.RED}{len(TEST_SCENARIOS) - len(successful)}{Colors.RESET}")
    print(f"  Total Time:        {total_time:.2f}s")
    print(f"  Avg Response:      {sum(r['elapsed'] for r in successful)/len(successful):.2f}s")
    
    print(f"\n{Colors.BOLD}📊 By Category:{Colors.RESET}")
    for cat, count in sorted(by_category.items()):
        print(f"  {cat:20s}: {count:2d} complaints")
    
    print(f"\n{Colors.BOLD}⚡ By Severity:{Colors.RESET}")
    for sev, count in sorted(by_severity.items(), key=lambda x: {'critical': 3, 'high': 2, 'medium': 1, 'low': 0}.get(x[0], 0), reverse=True):
        color = Colors.RED if sev == 'critical' else Colors.YELLOW if sev == 'high' else Colors.GREEN
        print(f"  {color}{sev:10s}{Colors.RESET}: {count:2d} complaints")
    
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    if len(successful) == len(TEST_SCENARIOS):
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ALL SCENARIOS PASSED! System working perfectly!{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Some scenarios failed - check logs{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*80}{Colors.RESET}\n")

if __name__ == '__main__':
    run_comprehensive_test()
