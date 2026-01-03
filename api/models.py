"""
Data Models - CampusVoice Complaint System
Version: 4.0.0 - Production Ready

Changes:
- ✅ Removed queue-based models
- ✅ Added status tracking
- ✅ Added visibility control (hidden_from)
- ✅ Added multiple image URLs support
- ✅ Added authority and student views
- ✅ Added monthly statistics
- ✅ Enhanced priority and routing metadata
- ✅ Fixed field ordering (required fields before optional)
- ✅ Fixed timezone deprecation (use timezone.utc)
- ✅ FIXED: SystemStatistics.to_dict() datetime/string handling
"""

from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import json


# =================== SUBMISSION MODEL ===================

@dataclass
class ComplaintSubmission:
    """
    Model for complaint submissions from students.
    Supports text complaint and optional image uploads.
    """
    roll_number: str  # Student roll number (will be hashed for pseudo-anonymity)
    department: str
    gender: str  # "male" | "female" | "other"
    residence: str  # "Hostel A" | "Day Scholar" | etc.
    complaint_text: str
    is_public: bool = False  # Whether to make it public for voting

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for processing"""
        return asdict(self)

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate submission data"""
        if not self.complaint_text or len(self.complaint_text.strip()) < 10:
            return False, "Complaint text must be at least 10 characters"
        
        if not self.roll_number or not self.roll_number.strip():
            return False, "Roll number is required"
        
        if not self.department or not self.department.strip():
            return False, "Department is required"
        
        if self.gender.lower() not in ["male", "female", "other"]:
            return False, "Invalid gender value"
        
        return True, None


# =================== MAIN COMPLAINT MODEL ===================

@dataclass
class Complaint:
    """
    Main complaint model stored in Firebase.
    Represents the complete complaint document with all metadata.
    
    IMPORTANT: All required fields (no default) must come BEFORE optional fields (with defaults)
    """
    # ========== REQUIRED FIELDS (NO DEFAULTS) ==========
    # Identity (pseudo-anonymous)
    complaint_id: str
    roll_number_hash: str  # Hashed roll number for pseudo-anonymity
    department: str
    gender: str
    residence: str
    
    # Complaint text
    original_text: str
    rephrased_text: str
    
    # Classification
    category: str  # "academic" | "hostel" | "infrastructure"
    assigned_authority: str  # MOVED HERE (before optional fields)
    
    # ========== OPTIONAL FIELDS (WITH DEFAULTS) ==========
    # Classification (optional)
    subcategory: Optional[str] = None  # Department name for academic, hostel name, etc.
    
    # Routing information
    routing_path: List[str] = field(default_factory=list)
    routing_reasoning: str = ""
    bypass_applied: bool = False
    escalated_to: Optional[str] = None
    hidden_from: List[str] = field(default_factory=list)  # Authorities who can't see this
    
    # Priority scoring
    priority_level: str = "Low"  # "Critical" | "High" | "Medium" | "Low"
    priority_score: float = 0.0
    priority_breakdown: List[str] = field(default_factory=list)
    priority_reasoning: str = ""
    priority_emoji: str = "🟢"
    
    # Image handling
    requires_image: bool = False
    is_mandatory_image: bool = False
    image_requirement_reason: Optional[str] = None
    image_urls: List[str] = field(default_factory=list)  # Firebase Storage URLs
    
    # Visibility (public/private/confidential)
    is_public: bool = False
    visibility_type: str = "private"  # "public" | "private" | "confidential"
    
    # Voting (for public complaints)
    upvotes: int = 0
    downvotes: int = 0
    net_votes: int = 0
    
    # Status tracking
    status: str = "raised"  # "raised" | "opened" | "reviewed" | "closed"
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timestamps (timezone-aware UTC)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    opened_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Processing metadata
    processing_time: float = 0.0
    llm_model_used: str = "groq"
    llm_confidence: str = "Medium"
    
    # Abusive language detection
    contains_abusive_language: bool = False
    language_issues: Optional[str] = None  # Description of language issues found

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase storage"""
        data = asdict(self)
        
        # Convert datetime objects to ISO format strings
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        
        if self.opened_at:
            data['opened_at'] = self.opened_at.isoformat()
        if self.reviewed_at:
            data['reviewed_at'] = self.reviewed_at.isoformat()
        if self.closed_at:
            data['closed_at'] = self.closed_at.isoformat()
        
        return data

    def update_status(self, new_status: str, updated_by: str, notes: Optional[str] = None):
        """Update complaint status and add to history"""
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)
        
        # Update specific timestamp
        if new_status == "opened":
            self.opened_at = datetime.now(timezone.utc)
        elif new_status == "reviewed":
            self.reviewed_at = datetime.now(timezone.utc)
        elif new_status == "closed":
            self.closed_at = datetime.now(timezone.utc)
        
        # Add to status history
        self.status_history.append({
            "status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "updated_by": updated_by,
            "notes": notes
        })

    def update_votes(self, upvotes: int, downvotes: int):
        """Update vote counts"""
        self.upvotes = upvotes
        self.downvotes = downvotes
        self.net_votes = upvotes - downvotes
        self.updated_at = datetime.now(timezone.utc)

    def add_image_url(self, image_url: str):
        """Add an image URL to the complaint"""
        if image_url not in self.image_urls:
            self.image_urls.append(image_url)
            self.updated_at = datetime.now(timezone.utc)


# =================== STATUS UPDATE MODEL ===================

@dataclass
class StatusUpdate:
    """
    Model for tracking status changes.
    Used in complaint status_history.
    """
    status: str
    timestamp: datetime
    updated_by: str  # Authority email or "system"
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "status": self.status,
            "timestamp": self.timestamp.isoformat(),
            "updated_by": self.updated_by,
            "notes": self.notes
        }


# =================== VIEW MODELS ===================

@dataclass
class StudentComplaintView:
    """
    Model for students viewing their own complaints.
    Shows tracking information without authority details.
    """
    complaint_id: str
    complaint_text: str  # Rephrased version
    category: str
    assigned_authority: str
    priority_level: str
    priority_emoji: str
    status: str
    status_display: str
    requires_image: bool
    image_urls: List[str]
    is_public: bool
    upvotes: int = 0
    downvotes: int = 0
    net_votes: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return asdict(self)


@dataclass
class AuthorityComplaintView:
    """
    Model for authorities viewing complaints assigned to them.
    Includes more details but respects pseudo-anonymity.
    """
    complaint_id: str
    original_text: str
    rephrased_text: str
    category: str
    department: str  # Complainant's department
    gender: str
    residence: str
    assigned_authority: str
    routing_path: List[str]
    routing_reasoning: str
    priority_level: str
    priority_score: float
    priority_breakdown: List[str]
    priority_emoji: str
    requires_image: bool
    image_urls: List[str]
    status: str
    status_history: List[Dict[str, Any]]
    is_public: bool
    subcategory: Optional[str] = None
    roll_number_hash: Optional[str] = None  # Only for Principal
    image_requirement_reason: Optional[str] = None
    upvotes: int = 0
    downvotes: int = 0
    created_at: str = ""
    updated_at: str = ""
    opened_at: Optional[str] = None
    reviewed_at: Optional[str] = None
    closed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return asdict(self)


@dataclass
class PublicComplaintView:
    """
    Model for public complaints visible to all students.
    Minimal information to protect privacy.
    """
    complaint_id: str
    complaint_text: str  # Rephrased version
    category: str
    department: str  # Complainant's department (for context)
    assigned_authority: str
    priority_level: str
    priority_emoji: str
    requires_image: bool
    image_urls: List[str]
    upvotes: int = 0
    downvotes: int = 0
    net_votes: int = 0
    status: str = "raised"
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return asdict(self)


# =================== VOTING MODELS ===================

@dataclass
class VoteRecord:
    """
    Model for tracking user votes on public complaints.
    Prevents duplicate voting.
    """
    vote_id: str
    complaint_id: str
    user_roll_hash: str  # Hashed roll number
    vote_type: str  # "upvote" | "downvote"
    voted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase storage"""
        return {
            "vote_id": self.vote_id,
            "complaint_id": self.complaint_id,
            "user_roll_hash": self.user_roll_hash,
            "vote_type": self.vote_type,
            "voted_at": self.voted_at.isoformat()
        }


@dataclass
class VoteUpdate:
    """
    Model for vote update requests.
    """
    complaint_id: str
    roll_number: str  # Will be hashed
    vote_type: str  # "upvote" | "downvote" | "remove"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# =================== STATISTICS MODELS ===================

@dataclass
class SystemStatistics:
    """
    Model for system-wide statistics and health metrics.
    """
    total_complaints: int = 0
    processed_complaints: int = 0
    public_complaints: int = 0
    private_complaints: int = 0
    confidential_complaints: int = 0
    
    # Status breakdown
    raised_count: int = 0
    opened_count: int = 0
    reviewed_count: int = 0
    closed_count: int = 0
    
    # Priority breakdown
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # Category breakdown
    academic_count: int = 0
    hostel_count: int = 0
    infrastructure_count: int = 0
    
    # Performance metrics
    average_processing_time: float = 0.0
    average_resolution_time: float = 0.0  # Hours to close
    total_upvotes: int = 0
    total_downvotes: int = 0
    
    # Last update timestamp
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        data = asdict(self)
        
        # ✅ FIXED: Handle both datetime and string types
        if isinstance(self.last_updated, datetime):
            data['last_updated'] = self.last_updated.isoformat()
        elif isinstance(self.last_updated, str):
            data['last_updated'] = self.last_updated  # Already a string
        else:
            # Fallback for any other type
            data['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        return data


@dataclass
class MonthlyStatistics:
    """
    Model for monthly statistics tracking.
    Stored as: statistics/monthly/{year_month}/
    """
    year_month: str  # Format: "2025-12"
    total_raised: int = 0
    total_closed: int = 0
    average_resolution_hours: float = 0.0
    
    # By category
    by_category: Dict[str, int] = field(default_factory=dict)
    
    # By priority
    by_priority: Dict[str, int] = field(default_factory=dict)
    
    # By authority
    by_authority: Dict[str, int] = field(default_factory=dict)
    
    # By department
    by_department: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firebase storage"""
        return asdict(self)


@dataclass
class AuthorityStatistics:
    """
    Statistics for a specific authority.
    """
    authority_name: str
    total_assigned: int = 0
    pending_count: int = 0
    closed_count: int = 0
    average_resolution_hours: float = 0.0
    critical_pending: int = 0
    high_pending: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# =================== HELPER FUNCTIONS ===================

def create_complaint_from_submission(
    submission: ComplaintSubmission,
    complaint_id: str,
    roll_number_hash: str
) -> Complaint:
    """
    Factory function to create a Complaint from a ComplaintSubmission.
    Initial state before processing.
    """
    return Complaint(
        complaint_id=complaint_id,
        roll_number_hash=roll_number_hash,
        department=submission.department,
        gender=submission.gender,
        residence=submission.residence,
        original_text=submission.complaint_text,
        rephrased_text="",  # Will be filled by LLM
        category="",  # Will be determined by LLM
        assigned_authority="",  # Will be determined by routing
        is_public=submission.is_public,
        status="raised",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


def complaint_to_student_view(complaint: Complaint) -> StudentComplaintView:
    """Convert Complaint to StudentComplaintView"""
    status_display_map = {
        "raised": "📝 Complaint Raised",
        "opened": "👁️ Opened by Authority",
        "reviewed": "⚙️ Under Review",
        "closed": "✅ Resolved & Closed"
    }
    
    return StudentComplaintView(
        complaint_id=complaint.complaint_id,
        complaint_text=complaint.rephrased_text,
        category=complaint.category,
        assigned_authority=complaint.assigned_authority,
        priority_level=complaint.priority_level,
        priority_emoji=complaint.priority_emoji,
        status=complaint.status,
        status_display=status_display_map.get(complaint.status, complaint.status),
        requires_image=complaint.requires_image,
        image_urls=complaint.image_urls,
        is_public=complaint.is_public,
        upvotes=complaint.upvotes,
        downvotes=complaint.downvotes,
        net_votes=complaint.net_votes,
        created_at=complaint.created_at.isoformat(),
        updated_at=complaint.updated_at.isoformat()
    )


def complaint_to_authority_view(
    complaint: Complaint,
    show_roll_number: bool = False
) -> AuthorityComplaintView:
    """
    Convert Complaint to AuthorityComplaintView.
    show_roll_number=True only for Principal.
    """
    return AuthorityComplaintView(
        complaint_id=complaint.complaint_id,
        original_text=complaint.original_text,
        rephrased_text=complaint.rephrased_text,
        category=complaint.category,
        subcategory=complaint.subcategory,
        department=complaint.department,
        gender=complaint.gender,
        residence=complaint.residence,
        roll_number_hash=complaint.roll_number_hash if show_roll_number else None,
        assigned_authority=complaint.assigned_authority,
        routing_path=complaint.routing_path,
        routing_reasoning=complaint.routing_reasoning,
        priority_level=complaint.priority_level,
        priority_score=complaint.priority_score,
        priority_breakdown=complaint.priority_breakdown,
        priority_emoji=complaint.priority_emoji,
        requires_image=complaint.requires_image,
        image_requirement_reason=complaint.image_requirement_reason,
        image_urls=complaint.image_urls,
        status=complaint.status,
        status_history=complaint.status_history,
        is_public=complaint.is_public,
        upvotes=complaint.upvotes,
        downvotes=complaint.downvotes,
        created_at=complaint.created_at.isoformat(),
        updated_at=complaint.updated_at.isoformat(),
        opened_at=complaint.opened_at.isoformat() if complaint.opened_at else None,
        reviewed_at=complaint.reviewed_at.isoformat() if complaint.reviewed_at else None,
        closed_at=complaint.closed_at.isoformat() if complaint.closed_at else None
    )


def complaint_to_public_view(complaint: Complaint) -> PublicComplaintView:
    """Convert Complaint to PublicComplaintView (for public feed)"""
    return PublicComplaintView(
        complaint_id=complaint.complaint_id,
        complaint_text=complaint.rephrased_text,
        category=complaint.category,
        department=complaint.department,
        assigned_authority=complaint.assigned_authority,
        priority_level=complaint.priority_level,
        priority_emoji=complaint.priority_emoji,
        requires_image=complaint.requires_image,
        image_urls=complaint.image_urls,
        upvotes=complaint.upvotes,
        downvotes=complaint.downvotes,
        net_votes=complaint.net_votes,
        status=complaint.status,
        created_at=complaint.created_at.isoformat()
    )
