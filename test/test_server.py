"""
STANDALONE TEST SERVER WITH REAL FIREBASE
Complete Firebase integration - no imports needed!
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import time

app = Flask(__name__)
CORS(app)

# Initialize Firebase
print("=" * 70)
print("🚀 CAMPUSVOICE TEST SERVER - FIREBASE EDITION")
print("=" * 70)

try:
    cred = credentials.Certificate('firebase-key.json')
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase initialized successfully!")
except Exception as e:
    print(f"❌ Firebase initialization failed: {e}")
    exit(1)

def generate_complaint_id():
    """Generate unique complaint ID"""
    timestamp = int(time.time() * 1000)
    return f"CPL_{timestamp}"

def simulate_llm_processing(data):
    """Simulate LLM processing of complaint"""
    category = data.get('category', 'general')
    severity = data.get('severity', 'medium')
    
    # Category mapping
    category_map = {
        'hostel': {
            'department': 'Hostel Management',
            'authority': 'Hostel Warden',
            'sub_category': 'facilities'
        },
        'academic': {
            'department': 'Academic Affairs',
            'authority': 'Head of Department',
            'sub_category': 'teaching'
        },
        'infrastructure': {
            'department': 'Facilities Management',
            'authority': 'Infrastructure Manager',
            'sub_category': 'maintenance'
        },
        'canteen': {
            'department': 'Food Services',
            'authority': 'Canteen Manager',
            'sub_category': 'food_quality'
        }
    }
    
    # Severity to priority mapping
    priority_map = {
        'critical': 9.5,
        'high': 8.0,
        'medium': 6.0,
        'low': 4.0
    }
    
    cat_info = category_map.get(category, {
        'department': 'General Administration',
        'authority': 'Admin Office',
        'sub_category': 'general'
    })
    
    return {
        'detected_category': category,
        'sub_category': cat_info['sub_category'],
        'assigned_authority': cat_info['authority'],
        'department': cat_info['department'],
        'priority_score': priority_map.get(severity, 5.0),
        'urgency_level': severity,
        'processing_time': datetime.utcnow().isoformat() + 'Z',
        'auto_assigned': True
    }

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'message': 'CampusVoice Test Server - Firebase Edition',
        'status': 'running',
        'firebase': 'connected',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

@app.route('/api/v1/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'firebase': 'connected',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })

@app.route('/api/v1/complaints', methods=['POST'])
def submit_complaint():
    """Submit complaint - REAL Firebase integration!"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data'}), 400
        
        # Generate complaint ID
        complaint_id = generate_complaint_id()
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Simulate LLM processing
        processing = simulate_llm_processing(data)
        
        # Prepare full complaint data
        complaint_data = {
            'complaint_id': complaint_id,
            'student_name': data.get('student_name'),
            'student_id': data.get('student_id'),
            'email': data.get('email'),
            'phone': data.get('phone'),
            'category': data.get('category'),
            'description': data.get('description'),
            'location': data.get('location'),
            'severity': data.get('severity'),
            'anonymous': data.get('anonymous', False),
            'status': 'pending',
            'created_at': timestamp,
            'updated_at': timestamp,
            'processing': processing,
            'timeline': [{
                'action': 'complaint_submitted',
                'timestamp': timestamp,
                'status': 'pending'
            }]
        }
        
        print(f"\n📥 Processing complaint: {complaint_id}")
        print(f"   Student: {data.get('student_name')}")
        print(f"   Category: {data.get('category')}")
        print(f"   Severity: {data.get('severity')}")
        print(f"   Assigned to: {processing['assigned_authority']}")
        
        # Save to Firebase
        db.collection('complaints').document(complaint_id).set(complaint_data)
        
        print(f"   ✅ Saved to Firebase!")
        
        return jsonify({
            'success': True,
            'message': 'Complaint received and processed',
            'data': {
                'complaint_id': complaint_id,
                'status': 'pending',
                'category': data.get('category'),
                'student_name': data.get('student_name'),
                'assigned_to': processing['assigned_authority'],
                'priority_score': processing['priority_score']
            },
            'timestamp': timestamp
        }), 201
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/v1/complaints/<complaint_id>', methods=['GET'])
def get_complaint(complaint_id):
    """Get complaint from Firebase"""
    try:
        doc = db.collection('complaints').document(complaint_id).get()
        
        if not doc.exists:
            return jsonify({
                'success': False,
                'message': 'Complaint not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': doc.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/v1/complaints', methods=['GET'])
def list_complaints():
    """List all complaints from Firebase"""
    try:
        complaints = []
        docs = db.collection('complaints').order_by('created_at', direction=firestore.Query.DESCENDING).limit(50).stream()
        
        for doc in docs:
            complaints.append(doc.to_dict())
        
        return jsonify({
            'success': True,
            'count': len(complaints),
            'data': complaints
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("\n🔥 Firebase connection established!")
    print("✅ Ready to process real complaints\n")
    print("=" * 70)
    print("Server: http://localhost:5000")
    print("=" * 70)
    print("\n📍 Endpoints:")
    print("  GET  / - Root")
    print("  GET  /api/v1/health - Health check")
    print("  POST /api/v1/complaints - Submit complaint")
    print("  GET  /api/v1/complaints - List all complaints")
    print("  GET  /api/v1/complaints/<id> - Get specific complaint")
    print("=" * 70)
    print("\n🚀 Starting server...\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
