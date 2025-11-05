"""
CampusVoice - Core Configuration Module
Optimized for Groq LLM with high concurrency support
Version: 4.0.0 - Production Ready

Changes from v3.0:
- ✂️ Removed all Ollama/local LLM code
- ✂️ Removed queue-based processing
- ✅ Added data retention configuration
- ✅ Added complaint status constants
- ✅ Added authority hierarchy and escalation
- ✅ Added visibility/hiding logic
- ✅ Added image detection configuration
- ✅ Added Firebase Storage settings
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Config:
    """
    Application configuration for CampusVoice grievance system
    Supports high concurrency, pseudo-anonymity, and intelligent routing
    """

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

    # =================== API CONFIGURATION ===================
    # API server settings
    api_host: str = field(default_factory=lambda: os.getenv('API_HOST', '0.0.0.0'))
    api_port: int = field(default_factory=lambda: int(os.getenv('API_PORT', '8000')))
    api_debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'False').lower() == 'true')

    # CORS settings
    cors_origins: List[str] = field(default_factory=lambda: [
        "http://localhost:3000",  # React/Next.js frontend
        "http://localhost:8501",  # Streamlit dashboard
        "http://localhost:8000",  # Local API testing
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:8000",
        "*"  # Allow all for development (restrict in production!)
    ])

    # =================== CONCURRENCY & PERFORMANCE ===================
    # High concurrency settings (NO QUEUE - process all at once)
    max_concurrent_complaints: int = 100  # Handle 100 complaints simultaneously
    processing_timeout: int = 120  # 2 minutes max per complaint
    firebase_timeout: int = 30  # Firebase operations timeout
    api_timeout: int = 60  # API request timeout

    # =================== COMPLAINT STATUS CONSTANTS ===================
    # Status tracking for complaint lifecycle
    complaint_statuses: List[str] = field(default_factory=lambda: [
        "raised",      # Initial state when complaint is submitted
        "opened",      # Authority has viewed the complaint
        "reviewed",    # Authority is working on it
        "closed"       # Complaint resolved/closed
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

    # =================== COMPLAINT CATEGORIES ===================
    # Major categories for routing
    categories: List[str] = field(default_factory=lambda: [
        "academic",
        "hostel",
        "infrastructure"
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
        "Artificial Intelligence and Data Science"
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
    # Keywords for confidential complaints → route to Disciplinary Committee
    privacy_keywords: List[str] = field(default_factory=lambda: [
        "harassment", "harass", "harassed", "ragging", "abuse", "abused",
        "corruption", "discrimination", "discriminate", "bribery", "bribe",
        "misconduct", "inappropriate", "sexual", "violence", "violent",
        "threat", "threaten", "assault", "assaulted", "bully", "bullying",
        "intimidate", "intimidation", "mental health", "depression",
        "anxiety", "suicide", "self harm", "molest", "molestation", "stalking"
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
    # Firebase credentials
    firebase_credentials_path: str = field(
        default_factory=lambda: os.getenv('FIREBASE_CREDENTIALS', 'firebase-key.json')
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

    # =================== VOTING SYSTEM ===================
    # Reddit-style voting configuration
    upvote_weight: float = 1.0
    downvote_weight: float = 1.0
    vote_threshold_medium_priority: int = 10  # 10 net votes = medium priority boost
    vote_threshold_high_priority: int = 30  # 30 net votes = high priority boost

    # =================== DEBUG & LOGGING ===================
    # Debug settings
    debug_mode: bool = field(
        default_factory=lambda: os.getenv('DEBUG', 'False').lower() == 'true'
    )
    log_level: str = field(
        default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO')
    )  # DEBUG, INFO, WARNING, ERROR

    def __post_init__(self):
        """Validate configuration after initialization"""
        print("🔧 Initializing CampusVoice Configuration v4.0...")
        print()

        # Validate Groq API key if Groq is enabled
        if self.use_groq and not self.groq_api_key:
            print("⚠️  WARNING: GROQ_API_KEY not set!")
            print("   Get your FREE key: https://console.groq.com")
            print("   Falling back to rule-based processing")
            self.use_groq = False

        # Ensure at least one processing method is available
        if not self.use_groq:
            print("✅ Using rule-based processing (no LLM configured)")
        else:
            print(f"✅ Groq LLM enabled: {self.groq_model}")

        # Log configuration summary
        if self.debug_mode:
            print()
            print("📋 Configuration Summary:")
            print(f"   🧠 LLM: {'Groq' if self.use_groq else 'Rule-based'}")
            print(f"   🌐 API: {self.api_host}:{self.api_port}")
            print(f"   🔄 Max concurrent: {self.max_concurrent_complaints}")
            print(f"   📸 Max image size: {self.max_image_size_mb}MB")
            print(f"   🗂️  Data retention: {self.data_retention_months} months")
            print(f"   🔥 Firebase: {self.firebase_credentials_path}")
            print(f"   📊 Status tracking: {len(self.complaint_statuses)} states")
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


# =================== GLOBAL CONFIG INSTANCE ===================
# Create singleton instance
config = Config()


# =================== HELPER FUNCTIONS ===================
def get_config() -> Config:
    """Get global configuration instance"""
    return config
