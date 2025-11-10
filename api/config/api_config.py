"""
API Configuration
Flask app configuration with security and environment variable support
Version: 4.0.0 - Production Ready

Changes:
- ✅ Removed queue-based settings
- ✅ Added concurrent processing configuration
- ✅ Added image upload settings
- ✅ Added endpoint paths
- ✅ Added pagination settings
- ✅ Added response formatting options
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class APIConfig:
    """
    Flask API configuration with secure defaults
    """

    # =================== SECURITY ===================
    # Secret key for Flask sessions (CHANGE IN PRODUCTION!)
    SECRET_KEY = os.getenv(
        'SECRET_KEY',
        'campus-grievance-portal-secret-key-2025-CHANGE-IN-PRODUCTION'
    )

    # CORS settings (for frontend integration)
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # =================== FIREBASE ===================
    # Firebase credentials path
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        'FIREBASE_CREDENTIALS_PATH',
        'firebase-key.json'
    )
    
    # Firebase Storage bucket
    FIREBASE_STORAGE_BUCKET = os.getenv(
        'FIREBASE_STORAGE_BUCKET',
        'campusvoice-images'
    )

    # =================== GROQ LLM ===================
    # Groq API key (REQUIRED for LLM processing)
    GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
    GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')
    GROQ_TIMEOUT = int(os.getenv('GROQ_TIMEOUT', '60'))
    GROQ_MAX_RETRIES = int(os.getenv('GROQ_MAX_RETRIES', '3'))

    # =================== FLASK CONFIG ===================
    # JSON response formatting
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True

    # Request limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max request size (for images)

    # Timeout settings
    REQUEST_TIMEOUT = 60  # 60 seconds

    # =================== CONCURRENT PROCESSING ===================
    # Process complaints concurrently (NO QUEUE!)
    MAX_CONCURRENT_COMPLAINTS = int(os.getenv('MAX_CONCURRENT_COMPLAINTS', '100'))
    PROCESSING_TIMEOUT = int(os.getenv('PROCESSING_TIMEOUT', '120'))  # 2 minutes per complaint
    
    # Batch processing for multiple submissions
    ENABLE_BATCH_PROCESSING = True
    MAX_BATCH_SIZE = 50  # Process up to 50 complaints at once

    # =================== IMAGE UPLOAD SETTINGS ===================
    # Image upload configuration
    ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
    MAX_IMAGE_SIZE_MB = 5
    MAX_IMAGES_PER_COMPLAINT = 5
    IMAGE_UPLOAD_FOLDER = 'complaint_images/{complaint_id}/'
    
    # Image compression
    COMPRESS_IMAGES = True
    IMAGE_MAX_WIDTH = 1920
    IMAGE_MAX_HEIGHT = 1080
    IMAGE_QUALITY = 85  # JPEG quality (1-100)

    # =================== API RATE LIMITING ===================
    # Rate limiting (per user based on roll number)
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    # Per-endpoint rate limits
    RATELIMIT_SUBMIT = "10 per hour"  # Complaint submission
    RATELIMIT_VOTE = "50 per hour"  # Voting on complaints
    RATELIMIT_VIEW = "100 per hour"  # Viewing complaints
    RATELIMIT_STATUS = "30 per hour"  # Status updates (authorities)

    # =================== PAGINATION ===================
    # Pagination settings for list endpoints
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Sorting options
    ALLOWED_SORT_FIELDS = ['created_at', 'priority_score', 'net_votes', 'status']
    DEFAULT_SORT_FIELD = 'created_at'
    DEFAULT_SORT_ORDER = 'desc'  # 'asc' or 'desc'

    # =================== ENDPOINT PATHS ===================
    # API endpoint base paths
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    
    # Student endpoints
    ENDPOINT_SUBMIT_COMPLAINT = f'{API_PREFIX}/complaints/submit'
    ENDPOINT_MY_COMPLAINTS = f'{API_PREFIX}/complaints/my'
    ENDPOINT_PUBLIC_COMPLAINTS = f'{API_PREFIX}/complaints/public'
    ENDPOINT_VOTE = f'{API_PREFIX}/complaints/vote'
    ENDPOINT_UPLOAD_IMAGE = f'{API_PREFIX}/complaints/image'
    
    # Authority endpoints
    ENDPOINT_AUTHORITY_COMPLAINTS = f'{API_PREFIX}/authority/complaints'
    ENDPOINT_AUTHORITY_UPDATE_STATUS = f'{API_PREFIX}/authority/status'
    ENDPOINT_AUTHORITY_STATS = f'{API_PREFIX}/authority/statistics'
    ENDPOINT_AUTHORITY_EXPORT = f'{API_PREFIX}/authority/export'
    
    # Admin endpoints (Principal only)
    ENDPOINT_ADMIN_STATS = f'{API_PREFIX}/admin/statistics'
    ENDPOINT_ADMIN_ALL_COMPLAINTS = f'{API_PREFIX}/admin/complaints'
    ENDPOINT_ADMIN_MONTHLY_STATS = f'{API_PREFIX}/admin/statistics/monthly'

    # =================== RESPONSE FORMATTING ===================
    # Standard response format
    RESPONSE_FORMAT = {
        'success': True,
        'data': None,
        'message': '',
        'errors': [],
        'meta': {}
    }
    
    # Include processing metadata in responses
    INCLUDE_PROCESSING_META = os.getenv('INCLUDE_PROCESSING_META', 'True').lower() == 'true'
    
    # Hide sensitive fields in responses
    HIDE_ROLL_NUMBER_FOR = ['hod', 'warden', 'deputy_warden', 'ao']  # Principal can see

    # =================== DATA RETENTION ===================
    # Auto-deletion settings (from core config)
    DATA_RETENTION_MONTHS = int(os.getenv('DATA_RETENTION_MONTHS', '6'))
    CLEANUP_SCHEDULE_CRON = os.getenv('CLEANUP_SCHEDULE_CRON', '0 2 * * *')  # 2 AM daily

    # =================== DEBUG MODE ===================
    # Debug mode (NEVER enable in production!)
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'

    # =================== LOGGING ===================
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'campus_voice.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Log all API requests
    LOG_REQUESTS = True
    LOG_RESPONSES = DEBUG  # Only in debug mode

    # =================== HEALTH CHECK ===================
    # Health check endpoint
    ENDPOINT_HEALTH = '/health'
    HEALTH_CHECK_INTERVAL = 60  # seconds

    # =================== VALIDATION ===================
    @classmethod
    def validate(cls):
        """Validate critical configuration"""
        errors = []

        # Check Firebase credentials exist
        if not os.path.exists(cls.FIREBASE_CREDENTIALS_PATH):
            errors.append(f"Firebase credentials not found: {cls.FIREBASE_CREDENTIALS_PATH}")

        # Warn if Groq API key is missing (non-critical - fallback to rule-based)
        if not cls.GROQ_API_KEY:
            print("⚠️  WARNING: GROQ_API_KEY not set. Using rule-based fallback.")

        # Error if secret key is default in production
        if not cls.DEBUG and "CHANGE-IN-PRODUCTION" in cls.SECRET_KEY:
            errors.append("SECRET_KEY must be changed in production!")

        # Validate image settings
        if cls.MAX_IMAGE_SIZE_MB > cls.MAX_CONTENT_LENGTH / (1024 * 1024):
            errors.append("MAX_IMAGE_SIZE_MB exceeds MAX_CONTENT_LENGTH")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def print_config(cls):
        """Print configuration summary (for debugging)"""
        print("=" * 60)
        print("🔧 CampusVoice API Configuration v4.0")
        print("=" * 60)
        print(f"  Debug: {'✅ Enabled' if cls.DEBUG else '❌ Disabled'}")
        print(f"  Groq API: {'✅ Configured' if cls.GROQ_API_KEY else '⚠️  Missing (using fallback)'}")
        print(f"  Firebase: {'✅ Found' if os.path.exists(cls.FIREBASE_CREDENTIALS_PATH) else '❌ Missing'}")
        print(f"  Rate Limiting: {'✅ Enabled' if cls.RATELIMIT_ENABLED else '❌ Disabled'}")
        print(f"  Max Request Size: {cls.MAX_CONTENT_LENGTH / (1024*1024):.0f} MB")
        print(f"  Max Image Size: {cls.MAX_IMAGE_SIZE_MB} MB")
        print(f"  Request Timeout: {cls.REQUEST_TIMEOUT}s")
        print(f"  Concurrent Processing: {cls.MAX_CONCURRENT_COMPLAINTS} complaints")
        print(f"  Batch Processing: {'✅ Enabled' if cls.ENABLE_BATCH_PROCESSING else '❌ Disabled'}")
        print(f"  Data Retention: {cls.DATA_RETENTION_MONTHS} months")
        print(f"  API Version: {cls.API_VERSION}")
        print("=" * 60)
        print()


# =================== HELPER FUNCTIONS ===================

def get_api_config() -> APIConfig:
    """Get API configuration instance"""
    return APIConfig()


def is_allowed_image_extension(filename: str) -> bool:
    """Check if image file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in APIConfig.ALLOWED_IMAGE_EXTENSIONS


def format_api_response(
    success: bool,
    data: any = None,
    message: str = '',
    errors: list[str] = None,
    meta: dict[str, any] = None
) -> dict[str, any]:
    """
    Format standardized API response.
    
    Args:
        success: Whether request was successful
        data: Response data
        message: Success/error message
        errors: List of error messages
        meta: Additional metadata (pagination, timing, etc.)
    
    Returns:
        Formatted response dictionary
    """
    return {
        'success': success,
        'data': data,
        'message': message,
        'errors': errors or [],
        'meta': meta or {}
    }
