from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import time

@dataclass
class AnonymousComplaintSubmission:
    """Model for pseudo-anonymous complaint submissions (email only)"""
    complaint_text: str
    user_department: str
    user_residence: Optional[str] = None
    user_email: Optional[str] = None  # Optional for full anonymity
    image_data: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class QueuedComplaint:
    """Model for raw complaints in processing queue"""
    complaint_id: str
    original_complaint: str
    user_department: str
    user_residence: Optional[str]
    user_email: Optional[str]
    image_data: Optional[str]
    created_at: datetime
    status: str = 'pending'
    queue_position: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class LLMProcessingResult:
    """Result from LLM processing with rephrasing and visibility determination"""
    complaint_id: str
    original_complaint: str
    rephrased_complaint: str
    llm_determined_visibility: str  # public, private, confidential
    classification: str  # academic, hostel, infrastructure
    subcategory: Optional[str]  # department name for academic
    final_authority: str
    routing_path: List[str]
    priority_level: str
    confidence: str
    reasoning: str
    processing_time: float
    model_used: str
    created_at: datetime
    processed_at: datetime
    user_department: str
    user_email: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['processed_at'] = self.processed_at.isoformat()
        return data

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
    user_email: Optional[str]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
