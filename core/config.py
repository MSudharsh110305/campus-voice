"""
CampusVoice - Core Configuration Module

Optimized for:
- Groq LLM with high concurrency support
- Celery background task processing
- Redis queue management
- Railway deployment (cloud hosting)
- Multi-client concurrent processing

Version: 5.0.0 - Production Ready with Async Architecture

Changes from v4.0:
- ✅ Added Redis & Celery configuration
- ✅ Added deployment environment settings
- ✅ Firebase credentials support (file + JSON env var)
- ✅ Enhanced voting system configuration
- ✅ Added task queue settings
- ✅ Production security settings
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Config:
    """
    Application configuration for CampusVoice grievance system
    
    Supports:
    - High concurrency (100+ simultaneous users)
    - Pseudo-anonymity
    - Intelligent routing
    - Background AI processing
    - Cloud deployment (Railway)
    """
    
    # =================== ENVIRONMENT & DEPLOYMENT ===================
    # Environment configuration
    environment: str = field(
        default_factory=lambda: os.getenv('ENV', 'development')
    )  # development | staging | production
    
    debug_mode: bool = field(
        default_factory=lambda: os.getenv('DEBUG', 'False').lower() == 'true'
    )
    
    # Security
    secret_key: str = field(
        default_factory=lambda: os.getenv('SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION')
    )
    
    # Allowed hosts for CORS
    allowed_hosts: List[str] = field(
        default_factory=lambda: os.getenv('ALLOWED_HOSTS', '*').split(',')
    )
    
    # =================== GROQ LLM SETTINGS ===================
    # Groq API configuration (PRIMARY - Fast cloud LLM)
    groq_api_key: str = field(default_factory=lambda: os.getenv('GROQ_API_KEY', ''))
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout: int = 60  # High timeout for reliability
    groq_max_retries: int = 3  # Retry on failures
    groq_temperature: float = 0.15  # Low for consistency
    groq_max_tokens: int = 500  # Reasonable limit for complaints
    
    # Fallback to rule-based if Groq fails
    use_groq: bool = True  # Set to False to use only rule-based
    
    # =================== REDIS & CELERY CONFIGURATION ===================
    # Redis connection (task queue broker)
    redis_url: str = field(
        default_factory=lambda: os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    )
    
    # Celery broker & result backend (defaults to redis_url if not set)
    celery_broker_url: Optional[str] = field(
        default_factory=lambda: os.getenv('CELERY_BROKER_URL', None)
    )
    celery_result_backend: Optional[str] = field(
        default_factory=lambda: os.getenv('CELERY_RESULT_BACKEND', None)
    )
    
    # Celery task configuration
    celery_task_timeout: int = 300  # 5 minutes max per task
    celery_max_retries: int = 3  # Retry failed tasks 3 times
    celery_retry_backoff: int = 5  # Wait 5 seconds between retries
    celery_task_track_started: bool = True  # Track task start time
    celery_task_time_limit: int = 600  # Hard limit: 10 minutes
    
    # Worker configuration
    celery_worker_concurrency: int = field(
        default_factory=lambda: int(os.getenv('CELERY_WORKERS', '4'))
    )  # Number of concurrent worker processes
    
    celery_worker_prefetch_multiplier: int = 2  # Tasks per worker to prefetch
    celery_worker_max_tasks_per_child: int = 1000  # Restart worker after N tasks
    
    # Task priorities
    celery_task_default_priority: int = 5  # Medium priority
    celery_task_high_priority: int = 9  # High priority tasks
    celery_task_low_priority: int = 1  # Low priority tasks
    
    # =================== API CONFIGURATION ===================
    # API server settings
    api_host: str = field(default_factory=lambda: os.getenv('API_HOST', '0.0.0.0'))
    api_port: int = field(default_factory=lambda: int(os.getenv('API_PORT', '5000')))
    
    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",  # React/Next.js frontend
        "http://localhost:8501",  # Streamlit dashboard
        "http://localhost:8000",  # Local API testing
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:8000",
        "*"  # Allow all for development (REMOVE in production!)
    ])
    
    # API timeouts
    api_timeout: int = 60  # API request timeout
    api_response_timeout: int = 30  # Response generation timeout
    
    # =================== CONCURRENCY & PERFORMANCE ===================
    # High concurrency settings (NO QUEUE - process all at once)
    max_concurrent_complaints: int = 100  # Handle 100 complaints simultaneously
    processing_timeout: int = 120  # 2 minutes max per complaint
    firebase_timeout: int = 30  # Firebase operations timeout
    
    # Request rate limiting (per user)
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv('RATE_LIMIT_PER_MINUTE', '20'))
    )
    rate_limit_per_hour: int = field(
        default_factory=lambda: int(os.getenv('RATE_LIMIT_PER_HOUR', '100'))
    )
    
    # =================== COMPLAINT STATUS CONSTANTS ===================
    # Status tracking for complaint lifecycle
    complaint_statuses: List[str] = field(default_factory=lambda: [
        "raised",    # Initial state when complaint is submitted
        "opened",    # Authority has viewed the complaint
        "reviewed",  # Authority is working on it
        "closed"     # Complaint resolved/closed
    ])
    
    # Status display names
    status_display: Dict[str, str] = field(default_factory=lambda: {
        "raised": "📝 Complaint Raised",
        "opened": "👁️ Opened by Authority",
        "reviewed": "⚙️ Under Review",
        "closed": "✅ Resolved & Closed"
    })
    
    # =================== DATA RETENTION & CLEANUP ===================
    # Auto-deletion configuration
    data_retention_months: int = field(
        default_factory=lambda: int(os.getenv('DATA_RETENTION_MONTHS', '6'))
    )  # Delete complaint logs after 6 months (configurable)
    
    cleanup_schedule_cron: str = "0 2 * * *"  # Run cleanup at 2 AM daily
    cleanup_enabled: bool = field(
        default_factory=lambda: os.getenv('CLEANUP_ENABLED', 'True').lower() == 'true'
    )
    
    # =================== COMPLAINT CATEGORIES ===================
    # Major categories for routing (ONLY 4 - as per spec)
    categories: List[str] = field(default_factory=lambda: [
        "academic",
        "hostel",
        "infrastructure",
        "disciplinary"  # Added for sensitive complaints
    ])
    
    # =================== DEPARTMENTS ===================
    departments: List[str] = field(default_factory=lambda: [
        "Electronics & Communication Engineering",
        "Computer Science & Engineering",
        "Robotics and Automation",
        "Mechanical Engineering",
        "Electrical & Electronics Engineering",
        "Electronics & Instrumentation Engineering",
        "Biomedical Engineering",
        "Aeronautical Engineering",
        "Civil Engineering",
        "Information Technology",
        "Management Studies",
        "Artificial Intelligence and Data Science",
        "M.Tech in Computer Science and Engineering"
    ])
    
    # Department aliases (short → full canonical names)
    dept_aliases: Dict[str, str] = field(default_factory=lambda: {
        "cse": "Computer Science & Engineering",
        "ece": "Electronics & Communication Engineering",
        "it": "Information Technology",
        "eee": "Electrical & Electronics Engineering",
        "ei": "Electronics & Instrumentation Engineering",
        "e&i": "Electronics & Instrumentation Engineering",
        "mech": "Mechanical Engineering",
        "mechanical": "Mechanical Engineering",
        "civil": "Civil Engineering",
        "biomedical": "Biomedical Engineering",
        "aero": "Aeronautical Engineering",
        "ai&ds": "Artificial Intelligence and Data Science",
        "aids": "Artificial Intelligence and Data Science",
        "robotics": "Robotics and Automation",
        "mba": "Management Studies",
        "management": "Management Studies"
    })
    
    # =================== AUTHORITY HIERARCHY & ESCALATION ===================
    # Authority escalation paths
    authority_hierarchy: Dict[str, str] = field(default_factory=lambda: {
        "warden": "deputy_warden",
        "deputy_warden": "senior_deputy_warden",
        "senior_deputy_warden": "principal",
        "hod": "principal",
        "ao": "principal",
        "faculty": "hod"
    })
    
    # Authority display names
    authority_display_names: Dict[str, str] = field(default_factory=lambda: {
        "warden": "Hostel Warden",
        "deputy_warden": "Deputy Warden",
        "senior_deputy_warden": "Senior Deputy Warden",
        "hod": "Head of Department",
        "ao": "Administrative Officer",
        "principal": "Principal (Admin)",
        "faculty": "Faculty Member",
        "disciplinary": "Student Counselor / Disciplinary Committee"
    })
    
    # Visibility control - complaints hidden from these authorities
    visibility_rules: Dict[str, List[str]] = field(default_factory=lambda: {
        "against_warden": ["warden"],
        "against_deputy_warden": ["warden", "deputy_warden"],
        "against_senior_deputy_warden": ["warden", "deputy_warden", "senior_deputy_warden"],
        "against_hod": ["hod"],  # HOD can't see complaints against them
        "against_faculty": [],  # HOD can see faculty complaints
        "against_ao": ["ao"]
    })
    
    # =================== KEYWORD DETECTION ===================
    # Authority-specific keywords for smart routing
    authority_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "hostel": [
            "hostel", "warden", "deputy", "mess", "room", "accommodation", "food",
            "dining", "laundry", "visitor", "gate", "security", "curfew", "noise",
            "roommate", "bed", "mattress", "cupboard", "locker"
        ],
        "academic": [
            "professor", "faculty", "teacher", "class", "lecture", "exam", "test",
            "marks", "grades", "syllabus", "assignment", "lab", "department", "hod",
            "curriculum", "teaching", "course", "academic", "staff", "study",
            "semester", "timetable", "attendance"
        ],
        "infrastructure": [
            "library", "canteen", "parking", "building", "maintenance", "repair",
            "wifi", "internet", "biometric", "system", "equipment", "facility",
            "restroom", "electricity", "water", "ac", "air conditioning", "drinking water",
            "broken", "damage", "leak", "crack", "toilet", "washroom"
        ]
    })
    
    # =================== DEPARTMENT-SPECIFIC EQUIPMENT (HOD) ===================
    # Keywords indicating department lab/equipment → route to HOD (not AO)
    department_equipment_keywords: List[str] = field(default_factory=lambda: [
        "lab", "laboratory", "oscilloscope", "soldering", "arduino", "raspberry pi",
        "3d printer", "cnc", "lathe", "printer", "workbench", "equipment",
        "instrument", "instruments", "department lab", "dept lab", "project lab",
        "multimeter", "voltmeter", "microscope", "test bench", "pcb", "breadboard",
        "robotic arm", "sensor", "actuator", "plc", "microcontroller", "fpga",
        "welding machine", "drilling machine", "milling machine", "grinder"
    ])
    
    # =================== BUILDING/FACILITY KEYWORDS (AO) ===================
    # General building/facility keywords → route to Administrative Officer
    ao_infrastructure_keywords: List[str] = field(default_factory=lambda: [
        "classroom", "class room", "toilet", "washroom", "restroom", "bathroom",
        "corridor", "hallway", "ceiling", "roof", "fan", "ac", "air conditioning",
        "electricity", "power", "lighting", "light", "bulb", "tube light",
        "ventilation", "plumbing", "water supply", "drinking water", "leak",
        "drainage", "road", "pathway", "parking", "gate", "entrance",
        "lift", "elevator", "building", "block", "auditorium", "seminar hall",
        "stairs", "staircase", "door", "window", "wall", "floor", "paint",
        "maintenance", "repair", "broken", "damaged", "water cooler",
        "water dispenser", "fire extinguisher", "cctv", "camera"
    ])
    
    # =================== BUILDING NAMES ===================
    building_names: List[str] = field(default_factory=lambda: [
        "a block", "b block", "c block", "it block", "ece block", "spark block",
        "cse block", "library", "mba block", "g block", "f block", "main block",
        "admin block", "mechanical block", "civil block", "eee block",
        "eie block", "biomedical block", "aero block", "workshop"
    ])
    
    # =================== SENSITIVE CONTENT DETECTION ===================
    # Keywords for confidential complaints → route to Disciplinary Committee ONLY (not principal)
    privacy_keywords: List[str] = field(default_factory=lambda: [
        "harassment", "harass", "harassed", "ragging", "abuse", "abused",
        "corruption", "discrimination", "discriminate", "bribery", "bribe",
        "misconduct", "inappropriate", "sexual", "violence", "violent",
        "threat", "threaten", "assault", "assaulted", "bully", "bullying",
        "intimidate", "intimidation", "mental health", "depression",
        "anxiety", "suicide", "self harm", "molest", "molestation", "stalking",
        "personal issue", "personal problem", "very personal", "private matter",
        "confidential issue", "sensitive matter"
    ])
    
    # =================== PRIORITY SCORING ===================
    # High priority indicators
    urgency_keywords: List[str] = field(default_factory=lambda: [
        "urgent", "emergency", "immediate", "critical", "serious", "asap",
        "right now", "quickly", "help", "please help", "dying", "severe"
    ])
    
    # Safety concerns (highest priority)
    safety_keywords: List[str] = field(default_factory=lambda: [
        "safety", "danger", "dangerous", "hazard", "hazardous", "unsafe",
        "fire", "electrical", "electric shock", "gas", "leak", "leakage",
        "broken", "collapse", "collapsed", "injury", "injured", "accident",
        "explosion", "smoke", "burning", "chemical", "toxic"
    ])
    
    # =================== IMAGE DETECTION KEYWORDS ===================
    # Keywords that require visual evidence
    image_required_keywords: List[str] = field(default_factory=lambda: [
        "broken", "damage", "damaged", "leak", "leaking", "crack", "cracked",
        "spoilt", "spoiled", "dirty", "unclean", "pest", "insects", "cockroach",
        "rat", "mouse", "mold", "mould", "fungus", "rust", "rusted", "stain",
        "torn", "ripped", "missing", "vandal", "vandalism", "graffiti",
        "fire", "smoke", "flood", "flooded", "water logging", "clogged",
        "food quality", "unhygienic", "expired", "rotten", "smell", "odor"
    ])
    
    # Image requirement priority (some keywords mandate images more than others)
    mandatory_image_keywords: List[str] = field(default_factory=lambda: [
        "fire", "broken", "damage", "leak", "unclean", "pest", "mold",
        "food quality", "unhygienic", "vandalism"
    ])
    
    # =================== VALIDATION & LIMITS ===================
    # Input validation
    min_complaint_length: int = 10  # Minimum characters
    max_complaint_length: int = 5000  # Maximum characters
    
    # Image upload limits
    max_image_size_mb: int = 5  # Maximum image size
    max_images_per_complaint: int = 5  # Max images allowed
    allowed_image_formats: List[str] = field(default_factory=lambda: [
        "jpg", "jpeg", "png", "webp"
    ])
    
    # Rate limiting (per user)
    max_complaints_per_hour: int = 10
    max_complaints_per_day: int = 50
    
    # =================== FIREBASE CONFIGURATION ===================
    # Firebase credentials - DUAL MODE (file for local, JSON for production)
    
    # Mode 1: Local development (file path)
    firebase_credentials_path: str = field(
        default_factory=lambda: os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-key.json')
    )
    
    # Mode 2: Production deployment (JSON string in environment variable)
    firebase_credentials_json: Optional[str] = field(
        default_factory=lambda: os.getenv('FIREBASE_CREDENTIALS_JSON', None)
    )
    
    # Firebase Storage (for images)
    firebase_storage_bucket: str = field(
        default_factory=lambda: os.getenv('FIREBASE_STORAGE_BUCKET', 'campusvoice-images')
    )
    
    image_upload_path: str = "complaint_images/{complaint_id}/"
    
    # Firestore collections
    collection_complaints: str = "complaints"
    collection_public_complaints: str = "public_complaints"
    collection_status_log: str = "complaint_status_log"
    collection_images: str = "complaint_images"
    collection_users: str = "users"
    collection_authorities: str = "authorities"
    collection_statistics: str = "statistics"
    
    # Firebase connection pooling
    firebase_max_connections: int = 100
    firebase_connection_timeout: int = 30
    
    # =================== VOTING SYSTEM (UPDATED) ===================
    # Reddit-style voting configuration with caps
    
    # Vote influence caps (as per your spec)
    max_upvote_influence: int = 10  # Max 10 upvotes counted for priority
    max_downvote_influence: int = 10  # Max 10 downvotes counted for priority
    
    # Point values per vote
    upvote_points_per_vote: int = 2  # Each upvote adds +2 points
    downvote_points_per_vote: int = 1  # Each downvote subtracts -1 point
    
    # Legacy fields (kept for backward compatibility)
    upvote_weight: float = 1.0
    downvote_weight: float = 1.0
    
    # Vote thresholds for priority boost (informational only)
    vote_threshold_medium_priority: int = 10  # 10 net votes
    vote_threshold_high_priority: int = 30  # 30 net votes
    
    # Anti-abuse measures
    vote_fraud_detection_enabled: bool = True
    max_votes_per_user_per_hour: int = 50  # Prevent vote spam
    
    # =================== DEBUG & LOGGING ===================
    # Log level configuration
    log_level: str = field(
        default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO')
    )  # DEBUG | INFO | WARNING | ERROR | CRITICAL
    
    log_format: str = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    log_date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Logging destinations
    log_to_file: bool = field(
        default_factory=lambda: os.getenv('LOG_TO_FILE', 'False').lower() == 'true'
    )
    log_file_path: str = field(
        default_factory=lambda: os.getenv('LOG_FILE_PATH', 'logs/campusvoice.log')
    )
    log_rotation_size_mb: int = 10  # Rotate log after 10MB
    log_backup_count: int = 5  # Keep 5 backup log files
    
    # Performance monitoring
    enable_performance_monitoring: bool = field(
        default_factory=lambda: os.getenv('ENABLE_MONITORING', 'True').lower() == 'true'
    )
    slow_query_threshold_ms: int = 1000  # Log queries slower than 1 second
    
    def __post_init__(self):
        """Enhanced validation and initialization after dataclass creation"""
        print("🔧 Initializing CampusVoice Configuration v5.0...")
        print()
        
        # Set Celery URLs from Redis if not explicitly provided
        if not self.celery_broker_url:
            self.celery_broker_url = self.redis_url
        if not self.celery_result_backend:
            self.celery_result_backend = self.redis_url
        
        # Validate Groq API key if Groq is enabled
        if self.use_groq and not self.groq_api_key:
            print("⚠️  WARNING: GROQ_API_KEY not set!")
            print("   Get your FREE key: https://console.groq.com")
            print("   Falling back to rule-based processing")
            self.use_groq = False
        
        # Validate Firebase credentials
        has_firebase_file = os.path.exists(self.firebase_credentials_path)
        has_firebase_json = bool(self.firebase_credentials_json)
        
        if not has_firebase_file and not has_firebase_json:
            print("⚠️  WARNING: No Firebase credentials found!")
            print(f"   Expected file: {self.firebase_credentials_path}")
            print("   Or set FIREBASE_CREDENTIALS_JSON environment variable")
        
        # Validate Redis connection
        if not self.redis_url:
            print("⚠️  WARNING: REDIS_URL not set!")
            print("   Background task processing will not work without Redis")
        
        # Environment-specific warnings
        if self.environment == 'production':
            if self.secret_key == 'dev-secret-key-CHANGE-IN-PRODUCTION':
                print("🚨 CRITICAL: Using default SECRET_KEY in production!")
                print("   Set a secure SECRET_KEY environment variable immediately!")
            
            if '*' in self.cors_origins:
                print("⚠️  WARNING: CORS allows all origins in production!")
                print("   Update CORS settings for security")
        
        # Ensure at least one processing method is available
        if not self.use_groq:
            print("✅ Using rule-based processing (no LLM configured)")
        else:
            print(f"✅ Groq LLM enabled: {self.groq_model}")
        
        # Log configuration summary
        if self.debug_mode:
            print()
            print("📋 Configuration Summary:")
            print(f"   🌍 Environment: {self.environment}")
            print(f"   🧠 LLM: {'Groq (' + self.groq_model + ')' if self.use_groq else 'Rule-based'}")
            print(f"   🌐 API: {self.api_host}:{self.api_port}")
            print(f"   🔄 Max concurrent: {self.max_concurrent_complaints}")
            print(f"   📸 Max image size: {self.max_image_size_mb}MB")
            print(f"   🗂️  Data retention: {self.data_retention_months} months")
            print(f"   🔥 Firebase: {'JSON env var' if has_firebase_json else self.firebase_credentials_path}")
            print(f"   📊 Status tracking: {len(self.complaint_statuses)} states")
            print(f"   🔴 Redis: {self.redis_url}")
            print(f"   👷 Celery workers: {self.celery_worker_concurrency}")
            print(f"   🔐 Secret key: {'***SET***' if self.secret_key != 'dev-secret-key-CHANGE-IN-PRODUCTION' else '⚠️ DEFAULT'}")
            print()
    
    def get_status_index(self, status: str) -> int:
        """Get numeric index of status for tracking progress"""
        try:
            return self.complaint_statuses.index(status)
        except ValueError:
            return -1
    
    def is_valid_status_transition(self, current: str, new: str) -> bool:
        """Check if status transition is valid (can only move forward)"""
        current_idx = self.get_status_index(current)
        new_idx = self.get_status_index(new)
        return new_idx > current_idx or new == current
    
    def get_authority_escalation(self, authority: str) -> Optional[str]:
        """Get the next authority in escalation hierarchy"""
        return self.authority_hierarchy.get(authority)
    
    def get_visibility_hidden_from(self, complaint_against: str) -> List[str]:
        """Get list of authorities who should not see this complaint"""
        return self.visibility_rules.get(f"against_{complaint_against}", [])
    
    def normalize_department(self, dept: str) -> str:
        """Normalize department name using aliases"""
        key = dept.strip().lower()
        return self.dept_aliases.get(key, dept.strip())
    
    def get_firebase_credentials(self) -> dict:
        """
        Get Firebase credentials from either file or environment variable.
        
        Returns:
            dict: Firebase credentials as a dictionary
        
        Raises:
            FileNotFoundError: If credentials file doesn't exist (in file mode)
            ValueError: If JSON credentials are invalid (in JSON mode)
        """
        import json
        
        # Priority 1: Use JSON from environment variable (production)
        if self.firebase_credentials_json:
            try:
                return json.loads(self.firebase_credentials_json)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid FIREBASE_CREDENTIALS_JSON: {e}")
        
        # Priority 2: Use file path (local development)
        if os.path.exists(self.firebase_credentials_path):
            with open(self.firebase_credentials_path, 'r') as f:
                return json.load(f)
        
        raise FileNotFoundError(
            f"Firebase credentials not found. "
            f"Set FIREBASE_CREDENTIALS_JSON or provide file at {self.firebase_credentials_path}"
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == 'development'


# =================== GLOBAL CONFIG INSTANCE ===================
# Create singleton instance
_config_instance = None


def get_config() -> Config:
    """
    Get global configuration instance (singleton pattern).
    
    Returns:
        Config: The global configuration object
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# Create default instance for backward compatibility
config = get_config()
 