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
from api.complaint_processor import ComplaintProcessor

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
        print("🔥 Firebase service initialized and attached to app")
    except Exception as e:
        print(f"❌ Failed to initialize Firebase: {e}")
        raise
    
    # Initialize and start complaint processor
    try:
        complaint_processor = ComplaintProcessor()
        complaint_processor.start_background_processing()
        app.complaint_processor = complaint_processor
        print("🤖 LLM Complaint Processor started in background")
    except Exception as e:
        print(f"❌ Failed to initialize complaint processor: {e}")
        raise
    
    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Root endpoint
    @app.route('/')
    def root():
        return {
            'service': 'Campus Grievance Portal API',
            'version': '1.0',
            'status': 'running',
            'firebase': 'connected',
            'llm_processor': 'active',
            'endpoints': {
                'health': '/api/v1/health',
                'submit_complaint': '/api/v1/complaints',
                'get_status': '/api/v1/complaints/{id}/status',
                'public_complaints': '/api/v1/complaints/public',
                'vote': '/api/v1/complaints/{id}/vote',
                'categories': '/api/v1/complaints/categories/{category}',
                'stats': '/api/v1/stats',
                'departments': '/api/v1/departments'
            }
        }
    
    # Cleanup on shutdown
    @app.teardown_appcontext
    def cleanup(error):
        if hasattr(app, 'complaint_processor'):
            app.complaint_processor.stop_processing()
    
    return app

if __name__ == '__main__':
    print("🏗️ CAMPUS GRIEVANCE PORTAL API")
    print("=" * 50)
    print("🔥 Firebase: Connecting...")
    print("🤖 LLM Processor: Initializing...")
    print("📡 API Server: Starting...")
    print("=" * 50)
    
    try:
        app = create_app()
        
        print("\n🚀 SYSTEM READY!")
        print("🔗 API Base URL: http://localhost:5000")
        print("📋 Health Check: http://localhost:5000/api/v1/health")
        print("📊 Statistics: http://localhost:5000/api/v1/stats")
        print("📝 Submit Complaint: POST /api/v1/complaints")
        print("🗳️ Vote on Complaint: POST /api/v1/complaints/{id}/vote")
        print("\n⏹️ Press Ctrl+C to stop all services")
        print("=" * 50)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
    except Exception as e:
        print(f"\n💥 Startup failed: {e}")
        import traceback
        traceback.print_exc()
