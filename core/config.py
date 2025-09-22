from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Config:
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_timeout: int = 1000

    # Models
    text_models: List[str] = field(default_factory=lambda: [
        "llama3:instruct", "qwen2.5:latest", "gemma2:2b-instruct"
    ])
    multimodal_models: List[str] = field(default_factory=lambda: [
        "llava:latest", "llava:13b"
    ])

    # Session flags
    current_model: Optional[str] = None
    is_multimodal: bool = False

    # Major categories
    authorities: List[str] = field(default_factory=lambda: [
        "hostel", "academic", "infrastructure"
    ])

    # Departments
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

    # Hostel hierarchy
    hostel_hierarchy: Dict[str, str] = field(default_factory=lambda: {
        "warden": "deputy_warden",
        "deputy_warden": "senior_deputy_warden"
    })

    # Bypass mapping for privacy/visibility text
    bypass_map: Dict[str, str] = field(default_factory=lambda: {
        "warden": "Deputy Warden",
        "deputy_warden": "Senior Deputy Warden"
    })

    # Authority-specific assistive keywords (used for support, not decision)
    authority_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "hostel": [
            "hostel", "warden", "deputy", "mess", "room", "accommodation", "food",
            "dining", "laundry", "visitor", "gate", "security"
        ],
        "academic": [
            "professor", "faculty", "teacher", "class", "lecture", "exam", "test",
            "marks", "grades", "syllabus", "assignment", "lab", "department", "hod",
            "curriculum", "teaching", "course", "academic", "staff"
        ],
        "infrastructure": [
            "library", "canteen", "parking", "building", "maintenance", "repair",
            "wifi", "internet", "biometric", "system", "equipment", "facility",
            "restroom", "electricity", "water", "ac", "air conditioning", "drinking water"
        ],
    })

    # College buildings for infrastructure detection
    building_names: List[str] = field(default_factory=lambda: [
        "a block", "b block", "c block", "it block", "ece block", "spark block",
        "cse block", "library", "mba block", "g block", "f block", "main block"
    ])

    # Facilities common in both hostel and college
    cross_facilities: List[str] = field(default_factory=lambda: [
        "bathroom", "restroom", "toilet", "washroom", "drinking water", "water dispenser"
    ])

    # Sensitive content detection
    privacy_keywords: List[str] = field(default_factory=lambda: [
        "harassment", "ragging", "abuse", "corruption", "discrimination",
        "bribery", "misconduct", "inappropriate", "sexual", "violence"
    ])

    # Priority scoring hints
    urgency_keywords: List[str] = field(default_factory=lambda: [
        "urgent", "emergency", "immediate", "critical", "serious", "asap"
    ])
    safety_keywords: List[str] = field(default_factory=lambda: [
        "safety", "danger", "hazard", "unsafe", "fire", "electrical", "gas", "leak"
    ])
