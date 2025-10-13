import os
import sys
from flask import Flask
from flask_cors import CORS

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from api.routes import api_bp
from api.config.api_config import APIConfig
from api.firebase_service import FirebaseService
from api.complaint_processor import IntelligentComplaintProcessor

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    CORS(app)

    # Load configuration
    app.config.from_object(APIConfig)

    # Initialize Firebase service
    try:
        firebase_service = FirebaseService()
        app.firebase_service = firebase_service
        print("🔥 Firebase service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        raise

    # Initialize and start intelligent complaint processor
    try:
        complaint_processor = IntelligentComplaintProcessor()
        complaint_processor.start_background_processing()
        app.complaint_processor = complaint_processor
        print("🧠 Intelligent LLM Complaint Processor started")
    except Exception as e:
        print(f"❌ Failed to initialize LLM processor: {e}")
        raise

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix='/api/v1')

    # Root endpoint
    @app.route('/')
    def root():
        return {
            'service': 'Campus Grievance Portal API v2.0',
            'type': 'Pseudo Anonymous with LLM Intelligence (text-only)',
            'features': [
                'User ID–based pseudo-anonymous submissions',
                'LLM-powered professional rephrasing',
                'Intelligent visibility determination',
                'Smart category classification',
                'Automatic authority routing with bypass handling'
            ],
            'privacy': [
                'Pseudo-anonymous (user_id identification, no email stored)',
                'LLM determines appropriate visibility levels',
                'Sensitive content automatically handled confidentially'
            ],
            'endpoints': {
                'health': '/api/v1/health',
                'submit_complaint': '/api/v1/complaints',
                'get_status': '/api/v1/complaints/{id}/status',
                'public_complaints': '/api/v1/complaints/public',
                'vote': '/api/v1/complaints/{id}/vote',
                'categories': '/api/v1/complaints/categories/{category}',
                'stats': '/api/v1/stats',
                'departments': '/api/v1/departments',
                'llm_capabilities': '/api/v1/llm/capabilities'
            }
        }

    # Cleanup on shutdown
    @app.teardown_appcontext
    def cleanup(error):
        if hasattr(app, 'complaint_processor'):
            app.complaint_processor.stop_processing()

    return app

if __name__ == '__main__':
    print("🏗️ CAMPUS GRIEVANCE PORTAL API v2.0")
    print("=" * 60)
    print("🎭 Type: Pseudo Anonymous with LLM Intelligence (text-only)")
    print("🔥 Firebase: Connecting...")
    print("🧠 LLM Processor: Initializing...")
    print("📡 API Server: Starting...")
    print("=" * 60)

    try:
        app = create_app()

        print("\n🚀 SYSTEM READY!")
        print("🔗 API Base URL: http://localhost:5000")
        print("📋 Health Check: http://localhost:5000/api/v1/health")
        print("📊 Statistics: http://localhost:5000/api/v1/stats")
        print("🧠 LLM Capabilities: http://localhost:5000/api/v1/llm/capabilities")
        print("\n📝 Submit Complaint: POST /api/v1/complaints")
        print("🗳️ Vote on Complaints: POST /api/v1/complaints/{id}/vote")
        print("\n🎭 PRIVACY FEATURES:")
        print("   • User ID–based pseudo-anonymous submissions")
        print("   • LLM-determined visibility levels")
        print("   • Automatic sensitive content protection")
        print("\n🧠 LLM INTELLIGENCE:")
        print("   • Professional complaint rephrasing")
        print("   • Smart visibility determination")
        print("   • Accurate category classification")
        print("   • Intelligent authority routing with bypass handling")
        print("\n⏹️ Press Ctrl+C to stop all services")
        print("=" * 60)

        app.run(debug=True, host='0.0.0.0', port=5000)

    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
    except Exception as e:
        print(f"\n💥 Startup failed: {e}")
        import traceback
        traceback.print_exc()
