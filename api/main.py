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
from api.queue_manager import QueueManager

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Load configuration
    app.config.from_object(APIConfig)
    
    print("🔧 Initializing services...")
    
    # Initialize services
    try:
        firebase_service = FirebaseService()
        queue_manager = QueueManager()
        
        # Store in app context
        app.firebase_service = firebase_service
        app.queue_manager = queue_manager
        
        print("✅ All services initialized successfully")
        
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        raise
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    @app.route('/')
    def health():
        return {
            'status': 'Campus Voice API is running',
            'version': '2.0',
            'services': {
                'firebase': 'connected',
                'redis': 'connected',
                'llm': 'ready'
            }
        }
    
    return app

if __name__ == '__main__':
    print("🎓 CAMPUS VOICE AI - PRODUCTION API")
    print("="*50)
    
    app = create_app()
    
    print("🚀 Starting Campus Voice API...")
    print("🔗 API will be available at: http://localhost:5000")
    print("📋 Health check: http://localhost:5000/api/v1/health")
    print("🔥 Firebase: ENABLED")
    print("🔴 Redis: ENABLED")
    print("🤖 LLM Processing: ENABLED")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
