"""
MINIMAL TEST SERVER - Guaranteed to Work
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timezone
import os
import sys

# Windows encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Create app
app = Flask(__name__)
CORS(app)

print("\n" + "="*70)
print("🚀 STARTING MINIMAL TEST SERVER")
print("="*70 + "\n")

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'CampusVoice Test Server',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/v1/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.route('/api/v1/complaints', methods=['POST'])
def submit_complaint():
    data = request.get_json()
    
    # Simple response
    return jsonify({
        'success': True,
        'message': 'Complaint received',
        'data': {
            'complaint_id': f'TEST_{datetime.now().timestamp()}',
            'student_name': data.get('student_name'),
            'category': data.get('category'),
            'status': 'received'
        },
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 201

if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000
    
    print(f"""
🌐 Server Starting...
   • URL: http://localhost:{PORT}
   • Health: http://localhost:{PORT}/api/v1/health
   • Submit: http://localhost:{PORT}/api/v1/complaints

Press Ctrl+C to stop
""")
    
    app.run(host=HOST, port=PORT, debug=True, threaded=True, use_reloader=False)
