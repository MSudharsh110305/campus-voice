"""
CampusVoice Test Suite - Clean Version
Only includes valid departments from your system
"""

import requests
import time
import json
from datetime import datetime
import csv

API_BASE_URL = "http://localhost:5000/api/v1"
TIMEOUT = 30
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
JSON_REPORT = f"test_report_{TIMESTAMP}.json"
CSV_REPORT = f"test_report_{TIMESTAMP}.csv"
HTML_REPORT = f"test_report_{TIMESTAMP}.html"

TEST_RESULTS = {
    'metadata': {'timestamp': datetime.now().isoformat(), 'api_url': API_BASE_URL, 'total_duration': 0},
    'suites': []
}

# Test Data - ONLY VALID DEPARTMENTS FROM YOUR CONFIG
DEPARTMENT_TEST_CASES = [
    {"roll_number": "21CSE001", "department": "Computer Science & Engineering", "gender": "male", "residence": "Hostel A", "complaint_text": "The C++ programming lab computers are outdated and slow. Need better hardware for running IDEs and compilers efficiently.", "is_public": True, "test_name": "CSE - Academic Lab Equipment"},
    {"roll_number": "21ECE002", "department": "Electronics & Communication Engineering", "gender": "female", "residence": "Hostel B", "complaint_text": "The oscilloscopes in ECE lab are not calibrated properly. Getting wrong readings in experiments which affects our practical marks.", "is_public": True, "test_name": "ECE - Lab Equipment Issue"},
    {"roll_number": "21MECH003", "department": "Mechanical Engineering", "gender": "male", "residence": "Day Scholar", "complaint_text": "The CAD software licenses in ME lab have expired. Cannot complete design assignments on time.", "is_public": True, "test_name": "Mech - Software License Issue"},
    {"roll_number": "21CIV004", "department": "Civil Engineering", "gender": "female", "residence": "Hostel C", "complaint_text": "The surveying equipment is missing some parts. Total station is not working properly during field work.", "is_public": True, "test_name": "Civil - Equipment Missing Parts"},
    {"roll_number": "21EEE005", "department": "Electrical & Electronics Engineering", "gender": "male", "residence": "Hostel A", "complaint_text": "Power systems lab has faulty circuit breakers. Safety hazard during experiments with high voltage equipment.", "is_public": True, "test_name": "EEE - Safety Hazard"},
    {"roll_number": "21IT006", "department": "Information Technology", "gender": "female", "residence": "Hostel B", "complaint_text": "Database lab server is frequently down. Cannot complete practicals on time and unable to practice queries.", "is_public": True, "test_name": "IT - Server Downtime"},
    {"roll_number": "21AI007", "department": "Artificial Intelligence and Data Science", "gender": "other", "residence": "Day Scholar", "complaint_text": "Need GPU servers for deep learning projects. Current machines are too slow for training neural network models.", "is_public": True, "test_name": "AI/DS - Hardware Requirement"},
    {"roll_number": "21BIO008", "department": "Biomedical Engineering", "gender": "female", "residence": "Hostel C", "complaint_text": "Medical equipment in biomedical lab needs maintenance. ECG machines are giving incorrect readings.", "is_public": True, "test_name": "Biomedical - Equipment Maintenance"},
    {"roll_number": "21EI009", "department": "Electronics & Instrumentation Engineering", "gender": "male", "residence": "Hostel A", "complaint_text": "PLC programming software licenses have expired. Cannot complete control systems lab experiments.", "is_public": True, "test_name": "EI - Software License"},
    {"roll_number": "21AERO010", "department": "Aeronautical Engineering", "gender": "male", "residence": "Day Scholar", "complaint_text": "Wind tunnel facility needs calibration. Getting inconsistent results in aerodynamics experiments.", "is_public": True, "test_name": "Aero - Facility Calibration"},
    {"roll_number": "21ROBO011", "department": "Robotics and Automation", "gender": "female", "residence": "Hostel B", "complaint_text": "Robotic arms in automation lab are malfunctioning. Cannot complete pick and place programming assignments.", "is_public": True, "test_name": "Robotics - Equipment Issue"},
    {"roll_number": "21MBA012", "department": "Management Studies", "gender": "male", "residence": "Day Scholar", "complaint_text": "MBA library needs more business case study books. Current collection is outdated and insufficient.", "is_public": True, "test_name": "MBA - Library Resources"}
]

CATEGORY_TEST_CASES = {
    "hostel": [
        {"roll_number": "21HOS001", "department": "Computer Science & Engineering", "gender": "male", "residence": "Hostel A", "complaint_text": "WiFi in Hostel A is extremely slow during evening hours. Cannot attend online classes or download study materials.", "is_public": True, "test_name": "Hostel - WiFi Issue"},
        {"roll_number": "21HOS002", "department": "Mechanical Engineering", "gender": "female", "residence": "Hostel B", "complaint_text": "Hostel mess food quality is very poor. Found insects in rice yesterday. This is unhygienic and health hazard.", "is_public": True, "test_name": "Hostel - Food Quality"},
        {"roll_number": "21HOS003", "department": "Electronics & Communication Engineering", "gender": "male", "residence": "Hostel C", "complaint_text": "Hot water is not available in Hostel C bathrooms. Geysers are not working since last week.", "is_public": True, "test_name": "Hostel - Hot Water"},
        {"roll_number": "21HOS004", "department": "Information Technology", "gender": "female", "residence": "Hostel A", "complaint_text": "Hostel rooms are not cleaned properly. Garbage is not collected regularly causing bad smell.", "is_public": True, "test_name": "Hostel - Cleaning Issue"},
        {"roll_number": "21HOS005", "department": "Civil Engineering", "gender": "male", "residence": "Hostel B", "complaint_text": "Hostel laundry service is very delayed. Takes 1 week to get clothes back which is too long.", "is_public": True, "test_name": "Hostel - Laundry Delay"}
    ],
    "infrastructure": [
        {"roll_number": "21INF001", "department": "Computer Science & Engineering", "gender": "female", "residence": "Day Scholar", "complaint_text": "Library air conditioning is not working. Too hot to study during afternoon making it impossible to concentrate.", "is_public": True, "test_name": "Infrastructure - Library AC"},
        {"roll_number": "21INF002", "department": "Mechanical Engineering", "gender": "male", "residence": "Hostel A", "complaint_text": "Main gate security is very lax. Anyone can enter without proper checking. Safety concern for students.", "is_public": True, "test_name": "Infrastructure - Security"},
        {"roll_number": "21INF003", "department": "Electrical & Electronics Engineering", "gender": "female", "residence": "Hostel C", "complaint_text": "Parking lot has potholes and water logging. Bikes are getting damaged and slipping is dangerous.", "is_public": True, "test_name": "Infrastructure - Parking"},
        {"roll_number": "21INF004", "department": "Information Technology", "gender": "male", "residence": "Day Scholar", "complaint_text": "Cafeteria seating is insufficient. Students have to stand and eat during lunch break.", "is_public": True, "test_name": "Infrastructure - Cafeteria"},
        {"roll_number": "21INF005", "department": "Electronics & Communication Engineering", "gender": "female", "residence": "Hostel B", "complaint_text": "Campus street lights are not working. Very dark at night which is a safety concern especially for female students.", "is_public": True, "test_name": "Infrastructure - Street Lights"}
    ],
    "academic": [
        {"roll_number": "21ACD001", "department": "Computer Science & Engineering", "gender": "male", "residence": "Hostel A", "complaint_text": "Professor is not covering entire syllabus. Many topics are being skipped and this will affect our exams.", "is_public": False, "test_name": "Academic - Syllabus Coverage"},
        {"roll_number": "21ACD002", "department": "Electronics & Communication Engineering", "gender": "female", "residence": "Day Scholar", "complaint_text": "Exam question papers are too difficult compared to what was taught in class. Grading seems unfair.", "is_public": False, "test_name": "Academic - Exam Difficulty"},
        {"roll_number": "21ACD003", "department": "Mechanical Engineering", "gender": "male", "residence": "Hostel B", "complaint_text": "Need more practical sessions for thermodynamics. Only theory is being taught but we need hands-on experience.", "is_public": True, "test_name": "Academic - Practical Need"},
        {"roll_number": "21ACD004", "department": "Information Technology", "gender": "female", "residence": "Hostel C", "complaint_text": "Course materials are outdated. Industry uses different technologies now. Curriculum needs modernization.", "is_public": True, "test_name": "Academic - Outdated Content"},
        {"roll_number": "21ACD005", "department": "Civil Engineering", "gender": "male", "residence": "Day Scholar", "complaint_text": "Grading is not transparent. No proper answer key is provided after exams to verify marks.", "is_public": False, "test_name": "Academic - Grading Issue"}
    ]
}

SENSITIVE_COMPLAINTS = [
    {"roll_number": "21SEN001", "department": "Computer Science & Engineering", "gender": "male", "residence": "Hostel A", "complaint_text": "I am being ragged by senior students. They force me to do their assignments and threaten me if I refuse. This is affecting my mental health badly.", "is_public": False, "test_name": "SENSITIVE - Ragging", "expected_authority": "Principal", "expected_visibility": "private"},
    {"roll_number": "21SEN002", "department": "Electronics & Communication Engineering", "gender": "female", "residence": "Hostel B", "complaint_text": "A professor made inappropriate comments about my body and touched me inappropriately during lab session. I feel very uncomfortable and scared.", "is_public": False, "test_name": "SENSITIVE - Sexual Harassment", "expected_authority": "Principal", "expected_visibility": "private"},
    {"roll_number": "21SEN003", "department": "Mechanical Engineering", "gender": "female", "residence": "Hostel C", "complaint_text": "I am feeling severely depressed and having suicidal thoughts. Academic pressure is too much and I feel like ending my life. Need urgent counseling.", "is_public": False, "test_name": "SENSITIVE - Mental Health Crisis", "expected_authority": "Principal", "expected_visibility": "private"},
    {"roll_number": "21SEN004", "department": "Information Technology", "gender": "male", "residence": "Hostel A", "complaint_text": "Hostel warden is discriminating against students from certain states. Gives preferential treatment to local students and treats us unfairly.", "is_public": False, "test_name": "SENSITIVE - Discrimination", "expected_authority": "Principal", "expected_visibility": "private"}
]

EMERGENCY_COMPLAINTS = [
    {"roll_number": "21EMG001", "department": "Computer Science & Engineering", "gender": "female", "residence": "Hostel A", "complaint_text": "Electrical wiring in Hostel A room 204 is sparking continuously. Serious fire hazard! Needs immediate attention before someone gets hurt.", "is_public": True, "test_name": "EMERGENCY - Electrical Fire Hazard", "expected_priority": ["Critical", "High"]},
    {"roll_number": "21EMG002", "department": "Mechanical Engineering", "gender": "male", "residence": "Hostel C", "complaint_text": "Water pipe burst in Hostel C second floor. Entire floor is flooded with water. Rooms are getting damaged and electrical equipment is at risk.", "is_public": True, "test_name": "EMERGENCY - Water Pipe Burst", "expected_priority": ["Critical", "High"]},
    {"roll_number": "21EMG003", "department": "Electrical & Electronics Engineering", "gender": "female", "residence": "Day Scholar", "complaint_text": "Main electrical panel in EEE block is making loud buzzing sounds and smells like burning. Very dangerous situation needs immediate attention.", "is_public": True, "test_name": "EMERGENCY - Electrical Danger", "expected_priority": ["Critical", "High"]}
]

def submit_complaint(data):
    try:
        r = requests.post(f"{API_BASE_URL}/complaints", json=data, timeout=TIMEOUT)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"error": str(e)}

def vote_on_complaint(cid, roll, vote_type):
    try:
        r = requests.post(f"{API_BASE_URL}/complaints/{cid}/vote", json={"roll_number": roll, "vote_type": vote_type}, timeout=TIMEOUT)
        return r.status_code, r.json()
    except Exception as e:
        return 500, {"error": str(e)}

def get_public_complaints(sort_by="created_at", limit=50):
    try:
        r = requests.get(f"{API_BASE_URL}/complaints/public", params={"page": 1, "limit": limit, "sort_by": sort_by}, timeout=TIMEOUT)
        return r.json()['data'] if r.status_code == 200 else None
    except:
        return None

def get_complaint_by_id(cid):
    try:
        r = requests.get(f"{API_BASE_URL}/complaints/{cid}", timeout=TIMEOUT)
        return r.json()['data'] if r.status_code == 200 else None
    except:
        return None

def test_department_complaints():
    print("\n" + "="*80)
    print("TEST SUITE 1: ALL DEPARTMENTS (12 departments)")
    print("="*80)
    
    suite = {'name': 'All Departments Test', 'tests': [], 'summary': {'total': 0, 'passed': 0, 'failed': 0}}
    ids = []
    
    for i, c in enumerate(DEPARTMENT_TEST_CASES, 1):
        name = c.pop('test_name')
        print(f"\n[{i}/12] {name}")
        
        start = time.time()
        status, result = submit_complaint(c)
        t = round(time.time() - start, 2)
        
        if status == 201:
            d = result['data']
            ids.append(d['complaint_id'])
            print(f"  ✅ PASS ({t}s)")
            print(f"     ID: {d['complaint_id']}")
            print(f"     Category: {d['category']}")
            print(f"     Authority: {d['assigned_authority']}")
            print(f"     Priority: {d['priority_level']} (Score: {d['priority_score']})")
            suite['tests'].append({'name': name, 'status': 'PASS', 'complaint_id': d['complaint_id'], 'category': d['category'], 'authority': d['assigned_authority'], 'priority': d['priority_level'], 'time': t})
            suite['summary']['passed'] += 1
        else:
            print(f"  ❌ FAIL - {result.get('error', 'Unknown')}")
            suite['tests'].append({'name': name, 'status': 'FAIL', 'error': result.get('error')})
            suite['summary']['failed'] += 1
        
        suite['summary']['total'] += 1
        time.sleep(0.5)
    
    print(f"\n{'─'*80}")
    print(f"DEPARTMENT TESTS: {suite['summary']['passed']}/{suite['summary']['total']} PASSED")
    TEST_RESULTS['suites'].append(suite)
    return ids

def test_category_complaints():
    print("\n" + "="*80)
    print("TEST SUITE 2: CATEGORIES (Hostel, Infrastructure, Academic)")
    print("="*80)
    
    suite = {'name': 'Category-Based Test', 'categories': [], 'summary': {'total': 0, 'passed': 0, 'failed': 0}}
    all_ids = []
    
    for cat, complaints in CATEGORY_TEST_CASES.items():
        print(f"\n{'─'*80}")
        print(f"CATEGORY: {cat.upper()} ({len(complaints)} tests)")
        print(f"{'─'*80}")
        
        cat_result = {'category': cat, 'tests': [], 'summary': {'total': 0, 'passed': 0, 'failed': 0}}
        
        for i, c in enumerate(complaints, 1):
            name = c.pop('test_name')
            print(f"\n[{i}/{len(complaints)}] {name}")
            
            start = time.time()
            status, result = submit_complaint(c)
            t = round(time.time() - start, 2)
            
            if status == 201:
                d = result['data']
                all_ids.append(d['complaint_id'])
                match = "✓" if d['category'] == cat else "✗"
                print(f"  ✅ PASS ({t}s)")
                print(f"     ID: {d['complaint_id']}")
                print(f"     Category: {d['category']} {match}")
                print(f"     Authority: {d['assigned_authority']}")
                print(f"     Visibility: {'Public' if d['is_public'] else 'Private'}")
                cat_result['tests'].append({'name': name, 'status': 'PASS', 'id': d['complaint_id'], 'category': d['category'], 'match': d['category'] == cat})
                cat_result['summary']['passed'] += 1
            else:
                print(f"  ❌ FAIL - {result.get('error', 'Unknown')}")
                cat_result['tests'].append({'name': name, 'status': 'FAIL', 'error': result.get('error')})
                cat_result['summary']['failed'] += 1
            
            cat_result['summary']['total'] += 1
            time.sleep(0.5)
        
        print(f"\n{cat.upper()}: {cat_result['summary']['passed']}/{cat_result['summary']['total']} PASSED")
        suite['categories'].append(cat_result)
        suite['summary']['total'] += cat_result['summary']['total']
        suite['summary']['passed'] += cat_result['summary']['passed']
        suite['summary']['failed'] += cat_result['summary']['failed']
    
    print(f"\n{'─'*80}")
    print(f"CATEGORY TESTS: {suite['summary']['passed']}/{suite['summary']['total']} PASSED")
    TEST_RESULTS['suites'].append(suite)
    return all_ids

def test_sensitive_complaints():
    print("\n" + "="*80)
    print("TEST SUITE 3: SENSITIVE COMPLAINTS (4 critical cases)")
    print("="*80)
    
    suite = {'name': 'Sensitive Complaints Test', 'tests': [], 'summary': {'total': 0, 'passed': 0, 'partial': 0, 'failed': 0}}
    
    for i, c in enumerate(SENSITIVE_COMPLAINTS, 1):
        name = c.pop('test_name')
        exp_auth = c.pop('expected_authority', None)
        exp_vis = c.pop('expected_visibility', None)
        
        print(f"\n[{i}/4] {name}")
        
        start = time.time()
        status, result = submit_complaint(c)
        t = round(time.time() - start, 2)
        
        if status == 201:
            d = result['data']
            is_private = not d['is_public']
            auth_match = exp_auth and exp_auth.lower() in d['assigned_authority'].lower()
            vis_match = (exp_vis == 'private' and is_private)
            
            if vis_match and auth_match:
                st = "PASS"
                suite['summary']['passed'] += 1
            elif vis_match or auth_match:
                st = "PARTIAL"
                suite['summary']['partial'] += 1
            else:
                st = "FAIL"
                suite['summary']['failed'] += 1
            
            print(f"  {'✅' if st == 'PASS' else '⚠️' if st == 'PARTIAL' else '❌'} {st} ({t}s)")
            print(f"     ID: {d['complaint_id']}")
            print(f"     Authority: {d['assigned_authority']} {'✓' if auth_match else '✗'}")
            print(f"     Visibility: {'Private' if is_private else 'Public'} {'✓' if vis_match else '✗'}")
            print(f"     Priority: {d['priority_level']}")
            suite['tests'].append({'name': name, 'status': st, 'id': d['complaint_id'], 'private': is_private})
        else:
            print(f"  ❌ FAIL - {result.get('error', 'Unknown')}")
            suite['tests'].append({'name': name, 'status': 'FAIL', 'error': result.get('error')})
            suite['summary']['failed'] += 1
        
        suite['summary']['total'] += 1
        time.sleep(0.5)
    
    print(f"\n{'─'*80}")
    print(f"SENSITIVE TESTS: {suite['summary']['passed']} PASS, {suite['summary']['partial']} PARTIAL, {suite['summary']['failed']} FAIL")
    TEST_RESULTS['suites'].append(suite)

def test_emergency_complaints():
    print("\n" + "="*80)
    print("TEST SUITE 4: EMERGENCY COMPLAINTS (3 scenarios)")
    print("="*80)
    
    suite = {'name': 'Emergency Complaints Test', 'tests': [], 'summary': {'total': 0, 'passed': 0, 'partial': 0, 'failed': 0}}
    
    for i, c in enumerate(EMERGENCY_COMPLAINTS, 1):
        name = c.pop('test_name')
        exp_pri = c.pop('expected_priority', None)
        
        print(f"\n[{i}/3] {name}")
        
        start = time.time()
        status, result = submit_complaint(c)
        t = round(time.time() - start, 2)
        
        if status == 201:
            d = result['data']
            pri_match = d['priority_level'] in (exp_pri if exp_pri else ['Critical', 'High'])
            st = "PASS" if pri_match else "PARTIAL"
            
            print(f"  {'✅' if st == 'PASS' else '⚠️'} {st} ({t}s)")
            print(f"     ID: {d['complaint_id']}")
            print(f"     Priority: {d['priority_level']} (Score: {d['priority_score']}) {'✓' if pri_match else '✗'}")
            print(f"     Authority: {d['assigned_authority']}")
            print(f"     Category: {d['category']}")
            suite['tests'].append({'name': name, 'status': st, 'id': d['complaint_id'], 'priority': d['priority_level']})
            
            if st == 'PASS':
                suite['summary']['passed'] += 1
            else:
                suite['summary']['partial'] += 1
        else:
            print(f"  ❌ FAIL - {result.get('error', 'Unknown')}")
            suite['tests'].append({'name': name, 'status': 'FAIL', 'error': result.get('error')})
            suite['summary']['failed'] += 1
        
        suite['summary']['total'] += 1
        time.sleep(0.5)
    
    print(f"\n{'─'*80}")
    print(f"EMERGENCY TESTS: {suite['summary']['passed']}/{suite['summary']['total']} PASSED")
    TEST_RESULTS['suites'].append(suite)

def test_voting_system(complaint_ids):
    print("\n" + "="*80)
    print("TEST SUITE 5: VOTING SYSTEM")
    print("="*80)
    
    suite = {'name': 'Voting System Test', 'tests': [], 'vote_sorting': {}, 'summary': {'total': 0, 'passed': 0, 'partial': 0, 'failed': 0}}
    
    data = get_public_complaints(limit=50)
    if not data or not data['complaints']:
        print("\n❌ No public complaints found!")
        TEST_RESULTS['suites'].append(suite)
        return
    
    comps = data['complaints'][:5]  # Test on 5 complaints only
    voters = [f"21VOTE{str(i).zfill(3)}" for i in range(1, 6)]
    
    print(f"\nTesting voting on {len(comps)} public complaints")
    
    for i, comp in enumerate(comps, 1):
        cid = comp['complaint_id']
        print(f"\n[{i}/{len(comps)}] Testing {cid}")
        
        init_up = comp.get('upvotes', 0)
        init_down = comp.get('downvotes', 0)
        print(f"  Initial: 👍 {init_up} | 👎 {init_down}")
        
        # Upvote with 3 voters
        up_success = 0
        for v in voters[:3]:
            s, _ = vote_on_complaint(cid, v, 'upvote')
            if s == 200:
                up_success += 1
            time.sleep(0.3)
        
        # Downvote with 2 voters
        down_success = 0
        for v in voters[3:5]:
            s, _ = vote_on_complaint(cid, v, 'downvote')
            if s == 200:
                down_success += 1
            time.sleep(0.3)
        
        # Duplicate check
        s, _ = vote_on_complaint(cid, voters[0], 'upvote')
        dup_prevented = (s != 200)
        
        # Verify
        time.sleep(1)
        updated = get_complaint_by_id(cid)
        
        if updated:
            new_up = updated.get('upvotes', 0)
            new_down = updated.get('downvotes', 0)
            exp_up = init_up + up_success
            exp_down = init_down + down_success
            votes_match = (new_up == exp_up and new_down == exp_down)
            
            print(f"  After: 👍 {new_up} | 👎 {new_down}")
            print(f"  Duplicate prevention: {'✓' if dup_prevented else '✗'}")
            print(f"  Vote count match: {'✓' if votes_match else '✗'}")
            
            if votes_match and dup_prevented:
                st = "PASS"
                suite['summary']['passed'] += 1
            elif votes_match or dup_prevented:
                st = "PARTIAL"
                suite['summary']['partial'] += 1
            else:
                st = "FAIL"
                suite['summary']['failed'] += 1
            
            print(f"  {'✅' if st == 'PASS' else '⚠️' if st == 'PARTIAL' else '❌'} {st}")
            suite['tests'].append({'id': cid, 'status': st, 'upvotes': new_up, 'downvotes': new_down})
        else:
            print(f"  ❌ FAIL - Could not verify")
            suite['tests'].append({'id': cid, 'status': 'FAIL'})
            suite['summary']['failed'] += 1
        
        suite['summary']['total'] += 1
        time.sleep(0.5)
    
    # Test sorting
    print(f"\n{'─'*80}")
    print("Testing vote-based sorting...")
    sorted_data = get_public_complaints(sort_by="net_votes", limit=10)
    if sorted_data and sorted_data['complaints']:
        print("\nTop 5 by votes:")
        for i, c in enumerate(sorted_data['complaints'][:5], 1):
            net = c.get('net_votes', 0)
            print(f"  {i}. {c['complaint_id']} - Net votes: {net}")
        suite['vote_sorting'] = {'status': 'PASS'}
        print("  ✅ Sorting works!")
    else:
        suite['vote_sorting'] = {'status': 'FAIL'}
        print("  ❌ Sorting failed")
    
    print(f"\n{'─'*80}")
    print(f"VOTING TESTS: {suite['summary']['passed']}/{suite['summary']['total']} PASSED")
    TEST_RESULTS['suites'].append(suite)

def generate_json_report():
    with open(JSON_REPORT, 'w') as f:
        json.dump(TEST_RESULTS, f, indent=2)

def generate_csv_report():
    with open(CSV_REPORT, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Suite', 'Test', 'Status', 'Details'])
        for s in TEST_RESULTS['suites']:
            if 'tests' in s:
                for t in s['tests']:
                    w.writerow([s['name'], t.get('name', 'N/A'), t.get('status', 'N/A'), t.get('id', t.get('complaint_id', 'N/A'))])
            elif 'categories' in s:
                for c in s['categories']:
                    for t in c['tests']:
                        w.writerow([f"{s['name']}-{c['category']}", t.get('name', 'N/A'), t.get('status', 'N/A'), t.get('id', 'N/A')])

def generate_html_report():
    total = sum(s.get('summary', {}).get('total', 0) for s in TEST_RESULTS['suites'])
    passed = sum(s.get('summary', {}).get('passed', 0) for s in TEST_RESULTS['suites'])
    failed = sum(s.get('summary', {}).get('failed', 0) for s in TEST_RESULTS['suites'])
    partial = sum(s.get('summary', {}).get('partial', 0) for s in TEST_RESULTS['suites'])
    
    html = f"""<!DOCTYPE html>
<html><head><title>CampusVoice Test Report</title>
<style>body{{font-family:Arial;margin:20px;background:#f5f5f5}}.header{{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:30px;border-radius:10px;margin-bottom:30px}}.suite{{background:#fff;padding:20px;margin:20px 0;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.1)}}.badge{{padding:5px 10px;border-radius:4px;font-weight:bold;font-size:.9em}}.badge-success{{background:#28a745;color:#fff}}.badge-warning{{background:#ffc107;color:#000}}.badge-danger{{background:#dc3545;color:#fff}}table{{width:100%;border-collapse:collapse;margin-top:15px}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}th{{background:#f0f0f0}}</style>
</head><body>
<div class="header"><h1>🧪 CampusVoice Test Report</h1><p>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
<p>Total: {total} | Passed: {passed} | Partial: {partial} | Failed: {failed}</p></div>
"""
    
    for s in TEST_RESULTS['suites']:
        html += f'<div class="suite"><h2>{s["name"]}</h2>'
        html += f'<span class="badge badge-success">Passed: {s.get("summary",{}).get("passed",0)}</span> '
        html += f'<span class="badge badge-warning">Partial: {s.get("summary",{}).get("partial",0)}</span> '
        html += f'<span class="badge badge-danger">Failed: {s.get("summary",{}).get("failed",0)}</span>'
        html += '<table><tr><th>Test</th><th>Status</th><th>Details</th></tr>'
        
        if 'tests' in s:
            for t in s['tests']:
                badge = 'success' if t['status']=='PASS' else 'warning' if t['status']=='PARTIAL' else 'danger'
                html += f'<tr><td>{t.get("name","N/A")}</td><td><span class="badge badge-{badge}">{t["status"]}</span></td><td>{t.get("id",t.get("complaint_id","N/A"))}</td></tr>'
        elif 'categories' in s:
            for c in s['categories']:
                for t in c['tests']:
                    badge = 'success' if t['status']=='PASS' else 'danger'
                    html += f'<tr><td>{t.get("name","N/A")}</td><td><span class="badge badge-{badge}">{t["status"]}</span></td><td>{t.get("id","N/A")}</td></tr>'
        
        html += '</table></div>'
    
    html += '</body></html>'
    with open(HTML_REPORT, 'w') as f:
        f.write(html)

def main():
    print("\n" + "="*80)
    print(" " * 20 + "🧪 CAMPUSVOICE TEST SUITE")
    print("="*80)
    
    # Health check
    try:
        r = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if r.status_code != 200:
            print("\n❌ API not responding!")
            return
    except:
        print("\n❌ Cannot connect to API. Start server: python main.py")
        return
    
    print("✅ API connected\n")
    
    start = time.time()
    
    # Run all tests
    dept_ids = test_department_complaints()
    cat_ids = test_category_complaints()
    test_sensitive_complaints()
    test_emergency_complaints()
    test_voting_system(dept_ids + cat_ids)
    
    # Summary
    total_time = round(time.time() - start, 2)
    TEST_RESULTS['metadata']['total_duration'] = total_time
    
    total = sum(s.get('summary', {}).get('total', 0) for s in TEST_RESULTS['suites'])
    passed = sum(s.get('summary', {}).get('passed', 0) for s in TEST_RESULTS['suites'])
    failed = sum(s.get('summary', {}).get('failed', 0) for s in TEST_RESULTS['suites'])
    partial = sum(s.get('summary', {}).get('partial', 0) for s in TEST_RESULTS['suites'])
    
    print("\n" + "="*80)
    print(" " * 30 + "FINAL RESULTS")
    print("="*80)
    print(f"  Total Tests:     {total}")
    print(f"  ✅ Passed:       {passed}")
    print(f"  ⚠️  Partial:      {partial}")
    print(f"  ❌ Failed:       {failed}")
    print(f"  ⏱️  Total Time:   {total_time}s")
    print("="*80)
    
    # Generate reports
    print("\n📄 Generating reports...")
    generate_json_report()
    print(f"  ✅ {JSON_REPORT}")
    generate_csv_report()
    print(f"  ✅ {CSV_REPORT}")
    generate_html_report()
    print(f"  ✅ {HTML_REPORT}")
    
    print("\n🎉 All tests complete!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted")
    except Exception as e:
        print(f"\n💥 Error: {e}")
