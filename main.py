"""
Main Application - CampusVoice Complaint System
Version: 4.0.0 - Production Ready (Windows Compatible)

Flask API server with:
- Complete REST API endpoints
- Concurrent request handling
- Windows console compatibility
- Firebase integration
- Groq LLM processing
- Debug logging
- CORS support
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
import traceback
from dotenv import load_dotenv

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import core modules
from core.config import get_config

# Import API modules
from api.routes import api_bp
from api.response_formatter import error_response
from api.firebase_service import FirebaseService
from api.intelligent_llm_engine import IntelligentLLMEngine
from api.complaint_processor import ComplaintProcessor


# =================== CONFIGURATION ===================

class Config:
    """Flask application configuration."""
    
    # Server configuration
    HOST = os.getenv('API_HOST', os.getenv('FLASK_HOST', '0.0.0.0'))
    PORT = int(os.getenv('API_PORT', os.getenv('FLASK_PORT', '5000')))
    DEBUG = os.getenv('DEBUG', os.getenv('FLASK_DEBUG', 'true')).lower() == 'true'
    
    # API configuration
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging configuration
    LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO
    LOG_FILE = os.getenv('LOG_FILE', 'campusvoice.log')
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5
    
    # Request configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Threading
    THREADED = True


# =================== FLASK APP FACTORY ===================

def create_app(config_class=Config):
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    configure_logging(app)
    
    # Configure CORS
    CORS(app, resources={
        f"{config_class.API_PREFIX}/*": {
            "origins": config_class.CORS_ORIGINS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Request-ID"],
            "expose_headers": ["X-Request-ID"],
            "supports_credentials": True
        }
    })
    
    # Initialize services
    initialize_services(app)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix=config_class.API_PREFIX)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register hooks
    register_hooks(app)
    
    # Root route
    @app.route('/')
    def index():
        return jsonify({
            'name': 'CampusVoice Complaint System',
            'version': '4.0.0',
            'api_version': config_class.API_VERSION,
            'status': 'running',
            'endpoints': {
                'api_base': config_class.API_PREFIX,
                'health': f"{config_class.API_PREFIX}/health",
                'submit': f"{config_class.API_PREFIX}/complaints"
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    return app


# =================== SERVICE INITIALIZATION ===================

def initialize_services(app):
    """Initialize all backend services."""
    app.logger.info("=" * 70)
    app.logger.info("CAMPUSVOICE COMPLAINT SYSTEM - STARTING UP")
    app.logger.info("=" * 70)
    app.logger.info("")
    
    try:
        # 1. Load configuration
        app.logger.info("Step 1: Loading configuration...")
        config = get_config()
        app.config_obj = config
        app.logger.info("   [OK] Configuration loaded")
        app.logger.info(f"   Departments: {len(config.departments)}")
        app.logger.info(f"   Categories: 3 (hostel, academic, infrastructure)")
        app.logger.info(f"   LLM Model: {config.groq_model}")
        
        if config.groq_api_key:
            app.logger.info("   [OK] Groq API Key: Configured")
        else:
            app.logger.warning("   [WARN] Groq API Key: NOT SET")
            app.logger.warning("   Set GROQ_API_KEY in .env for LLM features")
        app.logger.info("")
        
        # 2. Initialize Firebase
        app.logger.info("Step 2: Initializing Firebase Service...")
        firebase_service = FirebaseService()
        app.firebase_service = firebase_service
        app.logger.info("   [OK] Firebase Service initialized")
        app.logger.info(f"   Collections: {firebase_service.COMPLAINTS}, {firebase_service.VOTES}")
        app.logger.info("")
        
        # 3. Initialize LLM Engine
        app.logger.info("Step 3: Initializing LLM Engine...")
        llm_engine = IntelligentLLMEngine()
        app.llm_engine = llm_engine
        app.logger.info("   [OK] LLM Engine initialized")
        app.logger.info(f"   Status: {'Groq Available' if llm_engine.groq_available else 'Rule-based Fallback'}")
        app.logger.info(f"   Model: {llm_engine.groq_model if llm_engine.groq_available else 'Rule-based'}")
        app.logger.info("")
        
        # 4. Initialize Complaint Processor
        app.logger.info("Step 4: Initializing Complaint Processor...")
        complaint_processor = ComplaintProcessor()
        app.complaint_processor = complaint_processor
        app.logger.info("   [OK] Complaint Processor initialized")
        app.logger.info("")
        
        app.logger.info("=" * 70)
        app.logger.info("ALL SERVICES INITIALIZED SUCCESSFULLY")
        app.logger.info("=" * 70)
        app.logger.info("")
        app.logger.info("CampusVoice is ready to accept complaints!")
        app.logger.info(f"API Endpoint: http://{app.config['HOST']}:{app.config['PORT']}{Config.API_PREFIX}")
        app.logger.info(f"Debug Mode: {'ENABLED' if app.config['DEBUG'] else 'DISABLED'}")
        app.logger.info(f"Concurrent Processing: ENABLED")
        app.logger.info("")
        app.logger.info("=" * 70)
        app.logger.info("")
        
    except Exception as e:
        app.logger.error("=" * 70)
        app.logger.error("SERVICE INITIALIZATION FAILED")
        app.logger.error("=" * 70)
        app.logger.error(f"Error: {str(e)}")
        app.logger.error(traceback.format_exc())
        app.logger.error("=" * 70)
        raise


# =================== LOGGING CONFIGURATION ===================

def configure_logging(app):
    """Configure application logging with UTF-8 support."""
    app.logger.handlers.clear()
    app.logger.setLevel(app.config['LOG_LEVEL'])
    
    # Formatters
    detailed_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Console handler (UTF-8 for Windows)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(app.config['LOG_LEVEL'])
    if app.config['DEBUG']:
        console_handler.setFormatter(detailed_formatter)
    else:
        console_handler.setFormatter(simple_formatter)
    app.logger.addHandler(console_handler)
    
    # File handler
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    file_handler = RotatingFileHandler(
        f"logs/{app.config['LOG_FILE']}",
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT'],
        encoding='utf-8'  # UTF-8 for file
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    app.logger.addHandler(file_handler)
    
    # Werkzeug logger
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO if app.config['DEBUG'] else logging.WARNING)


# =================== ERROR HANDLERS ===================

def register_error_handlers(app):
    """Register global error handlers."""
    
    @app.errorhandler(400)
    def bad_request(e):
        app.logger.warning(f"400 Bad Request: {str(e)}")
        return error_response("Bad request", 400)
    
    @app.errorhandler(404)
    def not_found(e):
        app.logger.warning(f"404 Not Found: {str(e)}")
        return error_response("Resource not found", 404)
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        app.logger.warning(f"405 Method Not Allowed: {str(e)}")
        return error_response("Method not allowed", 405)
    
    @app.errorhandler(413)
    def request_entity_too_large(e):
        app.logger.warning(f"413 Payload Too Large: {str(e)}")
        return error_response("Request payload too large. Maximum: 16 MB", 413)
    
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"500 Internal Server Error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return error_response("Internal server error", 500)
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        app.logger.error(f"Unexpected error: {str(e)}")
        app.logger.error(traceback.format_exc())
        return error_response("An unexpected error occurred", 500)


# =================== REQUEST/RESPONSE HOOKS ===================

def register_hooks(app):
    """Register request/response hooks."""
    
    @app.before_request
    def log_request_info():
        if app.config['DEBUG']:
            from flask import request
            app.logger.debug("=" * 70)
            app.logger.debug(f"INCOMING REQUEST")
            app.logger.debug(f"   Method: {request.method}")
            app.logger.debug(f"   Path: {request.path}")
            app.logger.debug(f"   Remote: {request.remote_addr}")
            if request.args:
                app.logger.debug(f"   Query: {dict(request.args)}")
            app.logger.debug("=" * 70)
    
    @app.after_request
    def log_response_info(response):
        if app.config['DEBUG']:
            from flask import request
            app.logger.debug("=" * 70)
            app.logger.debug(f"OUTGOING RESPONSE")
            app.logger.debug(f"   Status: {response.status_code}")
            app.logger.debug(f"   Path: {request.path}")
            app.logger.debug("=" * 70)
        return response
    
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response


# =================== MAIN EXECUTION ===================

def main():
    """Main entry point."""
    try:
        app = create_app()
        
        app.logger.info("Starting Flask development server...")
        app.logger.info("")
        
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG'],
            threaded=app.config['THREADED'],
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n")
        if 'app' in locals():
            app.logger.info("Received shutdown signal (Ctrl+C)")
    except Exception as e:
        print(f"\nFatal error: {e}")
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    print("""
    ===================================================================
                                                                   
              CAMPUSVOICE COMPLAINT SYSTEM                  
                      Version 4.0.0                                
                                                                   
      Intelligent complaint management powered by Groq LLM             
                                                                   
    ===================================================================
    """)
    
    main()
