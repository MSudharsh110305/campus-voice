from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class ComplaintSubmissionModel:
    complaint_text: str
    user_department: str
    user_residence: Optional[str] = None
    user_email: Optional[str] = None
    user_phone: Optional[str] = None
    image_data: Optional[str] = None
    privacy_level: str = 'public'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class VoteModel:
    complaint_id: str
    user_id: str
    vote_type: str  # 'upvote' or 'downvote'
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
