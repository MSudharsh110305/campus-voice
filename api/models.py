from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

@dataclass
class ComplaintSubmission:
    """Model for incoming complaint submissions"""
    complaint_text: str
    user_department: str
    user_residence: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    image_data: Optional[str] = None
    visibility: str = 'public'  # public, private, confidential
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class QueuedComplaint:
    """Model for complaints in processing queue"""
    complaint_id: str
    complaint_text: str
    user_department: str
    user_residence: Optional[str]
    user_email: Optional[str]
    user_phone: Optional[str]
    image_data: Optional[str]
    image_description: Optional[str]
    visibility: str
    created_at: datetime
    status: str = 'pending'
    queue_position: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class ProcessedComplaint:
    """Model for LLM processed complaints"""
    complaint_id: str
    original_complaint: str
    rephrased_complaint: str
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
    visibility: str
    status: str = 'processed'
    user_department: str = ''
    user_email: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['processed_at'] = self.processed_at.isoformat()
        return data

@dataclass
class PublicComplaint:
    """Model for public complaints available for voting"""
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
class ComplaintVote:
    """Model for user votes on public complaints"""
    complaint_id: str
    user_id: str
    vote_type: str  # upvote, downvote
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
