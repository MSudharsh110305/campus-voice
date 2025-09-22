from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Config:
    """Configuration for Campus Voice AI System"""
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    ollama_timeout: int = 30
    
    # Available models
    text_models: List[str] = field(default_factory=lambda: [
        "llama3:instruct", "gemma3:latest", "qwen:latest", "gemma:2b"
    ])
    
    multimodal_models: List[str] = field(default_factory=lambda: [
        "llava:latest", "llava:13b", "llava:7b"
    ])
    
    # Current session settings
    current_model: Optional[str] = None
    is_multimodal: bool = False
    
    # Main authority categories - Only 3 as per requirement
    authorities: List[str] = field(default_factory=lambda: [
        "hostel", "academic", "infrastructure"
    ])
    
    # Academic departments - User selects their department first
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
    
    # Hostel authority hierarchy with bypass logic
    hostel_hierarchy: Dict[str, str] = field(default_factory=lambda: {
        "warden": "deputy_warden",
        "deputy_warden": "senior_deputy_warden"
    })
    
    # Authority-specific keywords for classification
    authority_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "hostel": [
            "hostel", "warden", "deputy", "mess", "room", "accommodation", "food", 
            "dining", "laundry", "visitor", "gate", "security", "bathroom", "shower"
        ],
        "academic": [
            "professor", "faculty", "teacher", "class", "lecture", "exam", "test",
            "marks", "grades", "syllabus", "assignment", "lab", "department", "hod",
            "curriculum", "teaching", "course", "academic"
        ],
        "infrastructure": [
            "library", "canteen", "parking", "building", "maintenance", "repair",
            "wifi", "internet", "biometric", "system", "equipment", "facility",
            "restroom", "electricity", "water", "ac", "air conditioning"
        ]
    })
    
    # Keywords for sensitive content detection
    sensitive_keywords: List[str] = field(default_factory=lambda: [
        "harassment", "ragging", "abuse", "corruption", "discrimination",
        "bribery", "misconduct", "inappropriate", "sexual", "violence"
    ])
    
    # Priority keywords
    urgency_keywords: List[str] = field(default_factory=lambda: [
        "urgent", "emergency", "immediate", "critical", "serious", "asap"
    ])
    
    safety_keywords: List[str] = field(default_factory=lambda: [
        "safety", "danger", "hazard", "unsafe", "fire", "electrical", "gas", "leak"
    ])
