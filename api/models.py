from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime

# =============== SUBMISSION & QUEUE MODELS ===============

@dataclass
class AnonymousComplaintSubmission:
    """
    Model for pseudo-anonymous complaint submissions (user_id required; no phone).
    Email removed; user_id, gender, residence are mandatory per new requirements.
    """
    complaint_text: str
    user_id: str
    user_department: str
    gender: str                 # e.g., "male" | "female" | "other"
    user_residence: str         # e.g., "Hostel A" | "Day Scholar"
    # Images removed as per "text complaints alone" directive

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class QueuedComplaint:
    """Model for raw complaints in processing queue"""
    complaint_id: str
    original_complaint: str
    user_id: str
    user_department: str
    gender: str
    user_residence: str
    created_at: datetime
    status: str = 'pending'
    queue_position: int = 0

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

# =============== PROCESSING RESULT MODELS ===============

@dataclass
class LLMProcessingResult:
    """Result from LLM processing with rephrasing and visibility determination"""
    complaint_id: str
    original_complaint: str
    rephrased_complaint: str
    llm_determined_visibility: str  # public, private, confidential
    classification: str             # academic, hostel, infrastructure
    subcategory: Optional[str]      # department name for academic
    final_authority: str
    routing_path: List[str]
    priority_level: str
    confidence: str
    reasoning: str
    processing_time: float
    model_used: str
    created_at: datetime
    processed_at: datetime
    user_id: str
    user_department: str
    gender: str
    user_residence: str

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['processed_at'] = self.processed_at.isoformat()
        return data

# =============== PUBLIC/PRIVATE VIEWS ===============

@dataclass
class PublicComplaint:
    """Model for public complaints available for community voting"""
    complaint_id: str
    rephrased_complaint: str
    classification: str
    final_authority: str
    priority_level: str
    department: str
    upvotes: int = 0
    downvotes: int = 0
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class PrivateComplaint:
    """Model for private/confidential complaints"""
    complaint_id: str
    original_complaint: str
    rephrased_complaint: str
    classification: str
    final_authority: str
    llm_determined_visibility: str
    user_id: str
    user_department: str
    gender: str
    user_residence: str
    created_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
