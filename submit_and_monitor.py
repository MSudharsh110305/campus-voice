#!/usr/bin/env python3
"""Campus Voice AI - Complaint Submission & Monitoring"""

import requests
import time
from datetime import datetime
import uuid

API_BASE_URL = "http://localhost:8000/api/v1"
POLL_INTERVAL = 2
MAX_WAIT_TIME = 120


class ComplaintMonitor:
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def submit_complaint(self, text, user_id=None, department=None, residence=None):
        """Submit complaint and extract ID from response"""
        if not user_id:
            user_id = f"student_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "complaint_text": text,
            "user_department": department or "Computer Science & Engineering",
            "user_residence": residence or "Hostel A",
            "user_id": user_id,
            "gender": "male"
        }
        
        try:
            print(f"\n{'='*80}")
            print(f"📝 SUBMITTING COMPLAINT")
            print(f"{'='*80}")
            print(f"User ID: {user_id}")
            print(f"Text: {text[:60]}...")
            print()
            
            response = self.session.post(
                f"{self.base_url}/complaints",
                json=payload,
                timeout=10
            )
            
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text[:200]}")  # Debug
            
            if response.status_code == 201:
                data = response.json()
                
                # Try different possible field names
                complaint_id = (
                    data.get('id') or 
                    data.get('complaint_id') or 
                    data.get('data', {}).get('id') or
                    data.get('data', {}).get('complaint_id')
                )
                
                if complaint_id:
                    print(f"\n✅ COMPLAINT QUEUED")
                    print(f"📋 Complaint ID: {complaint_id}")
                    print(f"⏱️  Submitted at: {datetime.now().strftime('%H:%M:%S')}\n")
                    return complaint_id
                else:
                    print(f"\n⚠️  Complaint submitted but no ID found in response:")
                    print(f"   Response: {data}")
                    return None
            else:
                print(f"\n❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def monitor_processing(self, complaint_id, timeout=MAX_WAIT_TIME):
        """Monitor until processed"""
        print(f"{'='*80}")
        print(f"⏳ MONITORING: {complaint_id}")
        print(f"{'='*80}\n")
        
        start_time = time.time()
        count = 0
        
        while time.time() - start_time < timeout:
            count += 1
            time.sleep(POLL_INTERVAL)
            
            try:
                response = self.session.get(
                    f"{self.base_url}/complaints/{complaint_id}/status",
                    timeout=10
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get('status', 'unknown')
                    elapsed = int(time.time() - start_time)
                    
                    if status == 'queued':
                        print(f"[{count}] ⏳ QUEUED ({elapsed}s)")
                    elif status == 'processing':
                        print(f"[{count}] 🧠 PROCESSING ({elapsed}s)")
                    elif status == 'completed':
                        print(f"[{count}] ✅ COMPLETED ({elapsed}s)\n")
                        print(f"🎉 SUCCESS!\n")
                        return True
                    elif status == 'failed':
                        print(f"[{count}] ❌ FAILED")
                        print(f"   Error: {status_data.get('error', 'Unknown')}\n")
                        return False
                else:
                    print(f"[{count}] ⏳ Waiting... (status endpoint returned {response.status_code})")
                    
            except Exception as e:
                print(f"[{count}] ⚠️  Error checking status: {e}")
        
        print(f"\n❌ TIMEOUT after {timeout}s\n")
        return False


def main():
    monitor = ComplaintMonitor()
    
    complaint_text = """The hostel mess food quality has deteriorated significantly. 
    Rice is undercooked and vegetables are not fresh."""
    
    print("\n" + "="*80)
    print("🎓 CAMPUS VOICE AI - SUBMISSION & MONITORING")
    print("="*80)
    print(f"API: {API_BASE_URL}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    
    complaint_id = monitor.submit_complaint(
        text=complaint_text,
        department="Computer Science & Engineering",
        residence="Hostel A"
    )
    
    if not complaint_id:
        print("\n❌ Submission failed or no ID received")
        print("   Check main.py logs for the complaint ID")
        print("   Or check Firebase console\n")
        return
    
    success = monitor.monitor_processing(complaint_id)
    
    if success:
        print(f"✅ DONE! ID: {complaint_id}\n")
    else:
        print(f"⚠️  Incomplete. Check main.py logs.\n")


if __name__ == "__main__":
    main()
