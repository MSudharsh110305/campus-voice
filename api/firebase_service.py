"""
Firebase Service - CampusVoice Complaint System
Version: 4.0.0 - Production Ready

Complete Firebase operations for complaint management:
- Firestore CRUD operations
- Firebase Storage for images
- Status tracking
- Voting system
- Statistics & analytics
- Data retention & cleanup
- Export functionality

Changes from v3.0:
- ✂️ REMOVED all queue-based code
- ✅ Added concurrent complaint processing
- ✅ Added Firebase Storage integration
- ✅ Added status tracking
- ✅ Added visibility filtering
- ✅ Added roll number hashing
- ✅ Added authority-specific queries
- ✅ Added student-specific queries
- ✅ Added monthly statistics
- ✅ Added data retention/cleanup
- ✅ Added export functionality
- ✅ Performance optimizations
"""

import firebase_admin
from firebase_admin import credentials, firestore, storage
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
import uuid
import hashlib
import csv
import io
from google.cloud.firestore_v1.base_query import FieldFilter

from api.models import (
    Complaint,
    ComplaintSubmission,
    StudentComplaintView,
    AuthorityComplaintView,
    PublicComplaintView,
    VoteRecord,
    SystemStatistics,
    MonthlyStatistics,
    AuthorityStatistics,
    complaint_to_student_view,
    complaint_to_authority_view,
    complaint_to_public_view
)

from core.config import get_config
config = get_config()


class FirebaseService:
    """
    Complete Firebase service for CampusVoice complaint management.
    Handles Firestore database and Firebase Storage operations.
    """
    
    def __init__(self, credentials_path: str = 'firebase-key.json'):
        """
        Initialize Firebase Admin SDK.
        
        Args:
            credentials_path: Path to Firebase service account key
        """
        # Initialize Firebase Admin SDK (singleton)
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': config.firebase_storage_bucket
                })
                print("🔥 Firebase initialized successfully")
            except Exception as e:
                print(f"❌ Firebase initialization failed: {e}")
                raise
        
        self.db = firestore.client()
        self.bucket = storage.bucket()
        
        # Collection names
        self.COMPLAINTS = config.collection_complaints
        self.PUBLIC_COMPLAINTS = config.collection_public_complaints
        self.STATUS_LOG = config.collection_status_log
        self.IMAGES = config.collection_images
        self.VOTES = 'complaint_votes'
        self.AUTHORITIES = config.collection_authorities
        self.STATISTICS = config.collection_statistics
        self.USERS = config.collection_users
        
        print("📊 Firebase collections ready")
        print(f"   📁 Main: {self.COMPLAINTS}")
        print(f"   📢 Public: {self.PUBLIC_COMPLAINTS}")
        print(f"   🗳️  Votes: {self.VOTES}")
        print(f"   📈 Statistics: {self.STATISTICS}")
    
    # =================== ROLL NUMBER HASHING ===================
    
    def hash_roll_number(self, roll_number: str) -> str:
        """
        Create SHA-256 hash of roll number for pseudo-anonymity.
        
        Args:
            roll_number: Student roll number
        
        Returns:
            Hashed roll number (64 chars hex)
        """
        return hashlib.sha256(roll_number.encode()).hexdigest()
    
    # =================== COMPLAINT CRUD OPERATIONS ===================
    
    def create_complaint(self, complaint: Complaint) -> bool:
        """
        Create a new complaint in Firestore.
        
        Args:
            complaint: Complaint object to save
        
        Returns:
            bool: Success status
        """
        try:
            # Save to main complaints collection
            doc_ref = self.db.collection(self.COMPLAINTS).document(complaint.complaint_id)
            doc_ref.set(complaint.to_dict())
            
            # If public, also save to public complaints collection (denormalized)
            if complaint.is_public:
                self._save_to_public_collection(complaint)
            
            # Initialize status log
            self._initialize_status_log(complaint.complaint_id)
            
            print(f"✅ Complaint created: {complaint.complaint_id}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to create complaint: {e}")
            return False
    
    def get_complaint(self, complaint_id: str) -> Optional[Complaint]:
        """
        Get a complaint by ID.
        
        Args:
            complaint_id: Complaint identifier
        
        Returns:
            Complaint object or None
        """
        try:
            doc = self.db.collection(self.COMPLAINTS).document(complaint_id).get()
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            return self._dict_to_complaint(data)
        
        except Exception as e:
            print(f"❌ Failed to get complaint: {e}")
            return None
    
    def update_complaint(self, complaint_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update complaint fields.
        
        Args:
            complaint_id: Complaint identifier
            updates: Dictionary of fields to update
        
        Returns:
            bool: Success status
        """
        try:
            # Add updated_at timestamp
            updates['updated_at'] = datetime.utcnow().isoformat()
            
            doc_ref = self.db.collection(self.COMPLAINTS).document(complaint_id)
            doc_ref.update(updates)
            
            # If public complaint, sync to public collection
            doc = doc_ref.get()
            if doc.exists and doc.to_dict().get('is_public'):
                complaint = self._dict_to_complaint(doc.to_dict())
                self._save_to_public_collection(complaint)
            
            print(f"✅ Complaint updated: {complaint_id}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to update complaint: {e}")
            return False
    
    def delete_complaint(self, complaint_id: str) -> bool:
        """
        Delete a complaint (soft delete by archiving).
        
        Args:
            complaint_id: Complaint identifier
        
        Returns:
            bool: Success status
        """
        try:
            # Move to archive instead of hard delete
            doc = self.db.collection(self.COMPLAINTS).document(complaint_id).get()
            
            if doc.exists:
                # Save to archive
                archive_ref = self.db.collection('archived_complaints').document(complaint_id)
                data = doc.to_dict()
                data['archived_at'] = datetime.utcnow().isoformat()
                archive_ref.set(data)
                
                # Delete from main collection
                doc.reference.delete()
                
                # Delete from public collection if exists
                self.db.collection(self.PUBLIC_COMPLAINTS).document(complaint_id).delete()
                
                print(f"✅ Complaint archived: {complaint_id}")
                return True
            
            return False
        
        except Exception as e:
            print(f"❌ Failed to delete complaint: {e}")
            return False
    
    # =================== STATUS MANAGEMENT ===================
    
    def update_status(
        self,
        complaint_id: str,
        new_status: str,
        updated_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update complaint status and track in history.
        
        Args:
            complaint_id: Complaint identifier
            new_status: New status (raised/opened/reviewed/closed)
            updated_by: Authority email/ID
            notes: Optional notes
        
        Returns:
            bool: Success status
        """
        try:
            complaint = self.get_complaint(complaint_id)
            if not complaint:
                return False
            
            # Update complaint status
            complaint.update_status(new_status, updated_by, notes)
            
            # Save to Firestore
            updates = {
                'status': new_status,
                'updated_at': datetime.utcnow().isoformat(),
                'status_history': complaint.status_history
            }
            
            # Update specific timestamp fields
            if new_status == 'opened':
                updates['opened_at'] = datetime.utcnow().isoformat()
            elif new_status == 'reviewed':
                updates['reviewed_at'] = datetime.utcnow().isoformat()
            elif new_status == 'closed':
                updates['closed_at'] = datetime.utcnow().isoformat()
            
            self.update_complaint(complaint_id, updates)
            
            # Log status change
            self._log_status_change(complaint_id, new_status, updated_by, notes)
            
            print(f"✅ Status updated: {complaint_id} → {new_status}")
            return True
        
        except Exception as e:
            print(f"❌ Failed to update status: {e}")
            return False
    
    def _initialize_status_log(self, complaint_id: str):
        """Initialize status log for a new complaint"""
        try:
            log_ref = self.db.collection(self.STATUS_LOG).document(complaint_id)
            log_ref.set({
                'complaint_id': complaint_id,
                'history': [{
                    'status': 'raised',
                    'timestamp': datetime.utcnow().isoformat(),
                    'updated_by': 'system',
                    'notes': 'Complaint submitted'
                }]
            })
        except Exception as e:
            print(f"⚠️  Failed to initialize status log: {e}")
    
    def _log_status_change(
        self,
        complaint_id: str,
        new_status: str,
        updated_by: str,
        notes: Optional[str]
    ):
        """Log status change to status log collection"""
        try:
            log_ref = self.db.collection(self.STATUS_LOG).document(complaint_id)
            log_ref.update({
                'history': firestore.ArrayUnion([{
                    'status': new_status,
                    'timestamp': datetime.utcnow().isoformat(),
                    'updated_by': updated_by,
                    'notes': notes
                }])
            })
        except Exception as e:
            print(f"⚠️  Failed to log status change: {e}")
    
    def get_status_history(self, complaint_id: str) -> List[Dict[str, Any]]:
        """Get complete status history for a complaint"""
        try:
            doc = self.db.collection(self.STATUS_LOG).document(complaint_id).get()
            if doc.exists:
                return doc.to_dict().get('history', [])
            return []
        except Exception as e:
            print(f"❌ Failed to get status history: {e}")
            return []
    
    # =================== IMAGE OPERATIONS ===================
    
    def upload_image(
        self,
        complaint_id: str,
        image_file,
        filename: str
    ) -> Optional[str]:
        """
        Upload image to Firebase Storage.
        
        Args:
            complaint_id: Complaint identifier
            image_file: File object or bytes
            filename: Original filename
        
        Returns:
            Public URL of uploaded image or None
        """
        try:
            # Generate unique filename
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            unique_filename = f"{complaint_id}/{uuid.uuid4()}.{ext}"
            
            # Upload to Firebase Storage
            blob = self.bucket.blob(f"complaint_images/{unique_filename}")
            
            if hasattr(image_file, 'read'):
                blob.upload_from_file(image_file, content_type=f'image/{ext}')
            else:
                blob.upload_from_string(image_file, content_type=f'image/{ext}')
            
            # Make public
            blob.make_public()
            url = blob.public_url
            
            # Save metadata
            self._save_image_metadata(complaint_id, url)
            
            print(f"✅ Image uploaded: {unique_filename}")
            return url
        
        except Exception as e:
            print(f"❌ Failed to upload image: {e}")
            return None
    
    def upload_multiple_images(
        self,
        complaint_id: str,
        image_files: List,
        filenames: List[str]
    ) -> List[str]:
        """
        Upload multiple images.
        
        Args:
            complaint_id: Complaint identifier
            image_files: List of file objects
            filenames: List of original filenames
        
        Returns:
            List of public URLs
        """
        urls = []
        for image_file, filename in zip(image_files, filenames):
            url = self.upload_image(complaint_id, image_file, filename)
            if url:
                urls.append(url)
        return urls
    
    def _save_image_metadata(self, complaint_id: str, image_url: str):
        """Save image metadata to Firestore"""
        try:
            img_ref = self.db.collection(self.IMAGES).document(complaint_id)
            img_ref.set({
                'complaint_id': complaint_id,
                'images': firestore.ArrayUnion([{
                    'url': image_url,
                    'uploaded_at': datetime.utcnow().isoformat()
                }])
            }, merge=True)
            
            # Update complaint image_urls
            complaint_ref = self.db.collection(self.COMPLAINTS).document(complaint_id)
            complaint_ref.update({
                'image_urls': firestore.ArrayUnion([image_url])
            })
        except Exception as e:
            print(f"⚠️  Failed to save image metadata: {e}")
    
    def get_image_urls(self, complaint_id: str) -> List[str]:
        """Get all image URLs for a complaint"""
        try:
            doc = self.db.collection(self.IMAGES).document(complaint_id).get()
            if doc.exists:
                images = doc.to_dict().get('images', [])
                return [img['url'] for img in images]
            return []
        except Exception as e:
            print(f"❌ Failed to get image URLs: {e}")
            return []
    
    def delete_images(self, complaint_id: str) -> bool:
        """Delete all images for a complaint"""
        try:
            # Delete from Storage
            blobs = self.bucket.list_blobs(prefix=f"complaint_images/{complaint_id}/")
            for blob in blobs:
                blob.delete()
            
            # Delete metadata
            self.db.collection(self.IMAGES).document(complaint_id).delete()
            
            print(f"✅ Images deleted for complaint: {complaint_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete images: {e}")
            return False
    
    # =================== STUDENT OPERATIONS ===================
    
    def get_student_complaints(
        self,
        roll_number: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[StudentComplaintView], int]:
        """
        Get complaints submitted by a student.
        
        Args:
            roll_number: Student roll number
            filters: Optional filters (status, category, etc.)
            page: Page number (1-indexed)
            limit: Items per page
        
        Returns:
            Tuple of (complaint views, total count)
        """
        try:
            roll_hash = self.hash_roll_number(roll_number)
            
            # Build query
            query = self.db.collection(self.COMPLAINTS).where(
                filter=FieldFilter('roll_number_hash', '==', roll_hash)
            )
            
            # Apply filters
            if filters:
                if 'status' in filters:
                    query = query.where(filter=FieldFilter('status', '==', filters['status']))
                if 'category' in filters:
                    query = query.where(filter=FieldFilter('category', '==', filters['category']))
            
            # Get total count
            total = len(list(query.stream()))
            
            # Apply pagination
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
            query = query.limit(limit).offset((page - 1) * limit)
            
            # Fetch complaints
            complaints = []
            for doc in query.stream():
                complaint = self._dict_to_complaint(doc.to_dict())
                view = complaint_to_student_view(complaint)
                complaints.append(view)
            
            return complaints, total
        
        except Exception as e:
            print(f"❌ Failed to get student complaints: {e}")
            return [], 0
    
    # =================== AUTHORITY OPERATIONS ===================
    
    def get_complaints_by_authority(
        self,
        authority_name: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 20
    ) -> Tuple[List[AuthorityComplaintView], int]:
        """
        Get complaints assigned to an authority with visibility filtering.
        Principal can see ALL complaints (not just assigned ones).
        
        Args:
            authority_name: Authority name (e.g., "Head of Department - CSE" or "Principal (Admin)")
            filters: Optional filters (status, priority, category)
            page: Page number
            limit: Items per page
        
        Returns:
            Tuple of (complaint views, total count)
        """
        try:
            # Principal can see ALL complaints, not just assigned ones
            is_principal = 'principal' in authority_name.lower()
            
            if is_principal:
                # Get ALL complaints for principal
                query = self.db.collection(self.COMPLAINTS)
            else:
                # Build query for assigned complaints only
                query = self.db.collection(self.COMPLAINTS).where(
                    filter=FieldFilter('assigned_authority', '==', authority_name)
                )
            
            # Apply filters
            if filters:
                if 'status' in filters:
                    query = query.where(filter=FieldFilter('status', '==', filters['status']))
                if 'priority' in filters:
                    query = query.where(filter=FieldFilter('priority_level', '==', filters['priority']))
                if 'category' in filters:
                    query = query.where(filter=FieldFilter('category', '==', filters['category']))
            
            # Get all results (we need to filter visibility in memory)
            all_docs = list(query.stream())
            
            # Filter by visibility (exclude complaints where authority is in hidden_from)
            filtered_complaints = []
            for doc in all_docs:
                complaint = self._dict_to_complaint(doc.to_dict())
                
                # Check if authority should see this complaint
                if self._can_view_complaint(complaint, authority_name):
                    filtered_complaints.append(complaint)
            
            total = len(filtered_complaints)
            
            # Sort by priority score (desc) then created_at (desc)
            filtered_complaints.sort(
                key=lambda c: (c.priority_score, c.created_at),
                reverse=True
            )
            
            # Apply pagination
            start = (page - 1) * limit
            end = start + limit
            paginated = filtered_complaints[start:end]
            
            # Convert to authority views
            # Only Principal can see roll_number_hash
            show_roll = 'principal' in authority_name.lower()
            views = [
                complaint_to_authority_view(c, show_roll_number=show_roll)
                for c in paginated
            ]
            
            return views, total
        
        except Exception as e:
            print(f"❌ Failed to get authority complaints: {e}")
            return [], 0
    
    def _can_view_complaint(self, complaint: Complaint, authority_name: str) -> bool:
        """Check if authority can view complaint (visibility filtering)"""
        # Principal can see ALL complaints (including those hidden from others)
        if 'principal' in authority_name.lower():
            return True
        
        # Extract authority type from name
        auth_type = authority_name.lower().split()[0] if authority_name else ""
        
        # Check if authority is in hidden_from list
        for hidden_auth in complaint.hidden_from:
            if hidden_auth.lower() in authority_name.lower():
                return False
        
        return True
    
    # =================== PUBLIC COMPLAINTS ===================
    
    def get_public_complaints(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        limit: int = 20,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Tuple[List[PublicComplaintView], int]:
        """
        Get public complaints with filtering and sorting.
        
        Args:
            filters: Optional filters (category, priority)
            page: Page number
            limit: Items per page
            sort_by: Sort field (created_at, net_votes, priority_score)
            sort_order: Sort order (asc, desc)
        
        Returns:
            Tuple of (complaint views, total count)
        """
        try:
            # Use denormalized public complaints collection for performance
            query = self.db.collection(self.PUBLIC_COMPLAINTS)
            
            # Apply filters
            if filters:
                if 'category' in filters:
                    query = query.where(filter=FieldFilter('category', '==', filters['category']))
                if 'priority' in filters:
                    query = query.where(filter=FieldFilter('priority_level', '==', filters['priority']))
            
            # Get total count
            total = len(list(query.stream()))
            
            # Apply sorting
            direction = firestore.Query.DESCENDING if sort_order == 'desc' else firestore.Query.ASCENDING
            if sort_by in ['created_at', 'net_votes']:
                query = query.order_by(sort_by, direction=direction)
            else:
                # Default to created_at
                query = query.order_by('created_at', direction=firestore.Query.DESCENDING)
            
            # Apply pagination
            query = query.limit(limit).offset((page - 1) * limit)
            
            # Fetch complaints
            views = []
            for doc in query.stream():
                data = doc.to_dict()
                
                # ✅ FIXED: Use .get() with defaults for all fields
                view = PublicComplaintView(
                    complaint_id=data.get('complaint_id', ''),
                    complaint_text=data.get('complaint_text', data.get('rephrased_text', data.get('original_text', ''))),
                    category=data.get('category', 'infrastructure'),  # ✅ FIXED
                    department=data.get('department', 'Unknown'),      # ✅ FIXED
                    assigned_authority=data.get('assigned_authority', 'Unknown'),  # ✅ FIXED
                    priority_level=data.get('priority_level', 'Low'),  # ✅ FIXED
                    priority_emoji=data.get('priority_emoji', '🟢'),
                    requires_image=data.get('requires_image', False),
                    image_urls=data.get('image_urls', []),
                    upvotes=data.get('upvotes', 0),
                    downvotes=data.get('downvotes', 0),
                    net_votes=data.get('net_votes', 0),
                    status=data.get('status', 'raised'),
                    created_at=data.get('created_at', '')
                )
                views.append(view)
            
            return views, total
        
        except Exception as e:
            print(f"❌ Failed to get public complaints: {e}")
            import traceback
            traceback.print_exc()  # ✅ ADDED: Print full traceback for debugging
            return [], 0
    
    def _save_to_public_collection(self, complaint: Complaint):
        """Save complaint to denormalized public collection"""
        try:
            if not complaint.is_public:
                return
            
            public_view = complaint_to_public_view(complaint)
            doc_ref = self.db.collection(self.PUBLIC_COMPLAINTS).document(complaint.complaint_id)
            doc_ref.set(public_view.to_dict())
            
            print(f"✅ Saved to public collection: {complaint.complaint_id}")  # ✅ ADDED: Confirmation log
        
        except Exception as e:
            print(f"⚠️  Failed to save to public collection: {e}")
            import traceback
            traceback.print_exc()  # ✅ ADDED: Print full traceback
    
    # =================== VOTING OPERATIONS ===================
    
    def vote_on_complaint(
        self,
        complaint_id: str,
        roll_number: str,
        vote_type: str
    ) -> Dict[str, Any]:
        """
        Record vote on a public complaint.
        
        Args:
            complaint_id: Complaint identifier
            roll_number: Voter's roll number
            vote_type: 'upvote', 'downvote', or 'remove'
        
        Returns:
            Dict with success status and message
        """
        try:
            # Check if complaint is public
            complaint = self.get_complaint(complaint_id)
            if not complaint:
                return {'success': False, 'message': 'Complaint not found'}
            
            if not complaint.is_public:
                return {'success': False, 'message': 'Complaint is not public. Only public complaints can be voted on.'}
            
            roll_hash = self.hash_roll_number(roll_number)
            vote_id = f"{complaint_id}_{roll_hash}"
            
            # Get existing vote
            vote_doc = self.db.collection(self.VOTES).document(vote_id).get()
            
            if vote_type == 'remove':
                # Remove vote
                if vote_doc.exists:
                    old_vote = vote_doc.to_dict()['vote_type']
                    vote_doc.reference.delete()
                    
                    # Update complaint counts
                    if old_vote == 'upvote':
                        self._update_vote_counts(complaint_id, -1, 0)
                    else:
                        self._update_vote_counts(complaint_id, 0, -1)
                    
                    return {'success': True, 'message': 'Vote removed'}
                return {'success': False, 'message': 'No vote to remove'}
            
            # Add or update vote
            if vote_doc.exists:
                old_vote = vote_doc.to_dict()['vote_type']
                if old_vote == vote_type:
                    return {'success': False, 'message': 'Already voted this way'}
                
                # Change vote
                vote_doc.reference.update({
                    'vote_type': vote_type,
                    'updated_at': datetime.utcnow().isoformat()
                })
                
                # Update counts
                if old_vote == 'upvote' and vote_type == 'downvote':
                    self._update_vote_counts(complaint_id, -1, 1)
                elif old_vote == 'downvote' and vote_type == 'upvote':
                    self._update_vote_counts(complaint_id, 1, -1)
            else:
                # New vote
                vote_record = VoteRecord(
                    vote_id=vote_id,
                    complaint_id=complaint_id,
                    user_roll_hash=roll_hash,
                    vote_type=vote_type
                )
                self.db.collection(self.VOTES).document(vote_id).set(vote_record.to_dict())
                
                # Update counts
                if vote_type == 'upvote':
                    self._update_vote_counts(complaint_id, 1, 0)
                else:
                    self._update_vote_counts(complaint_id, 0, 1)
            
            return {'success': True, 'message': 'Vote recorded successfully'}
        
        except Exception as e:
            print(f"❌ Failed to record vote: {e}")
            import traceback
            traceback.print_exc()  # ✅ ADDED: Print full traceback
            return {'success': False, 'message': f'Voting error: {str(e)}'}
    
    def _update_vote_counts(self, complaint_id: str, upvote_delta: int, downvote_delta: int):
        """Update vote counts for a complaint"""
        try:
            # Update main collection
            complaint_ref = self.db.collection(self.COMPLAINTS).document(complaint_id)
            complaint_ref.update({
                'upvotes': firestore.Increment(upvote_delta),
                'downvotes': firestore.Increment(downvote_delta),
                'net_votes': firestore.Increment(upvote_delta - downvote_delta),
                'updated_at': datetime.utcnow().isoformat()
            })
            
            # Update public collection
            public_ref = self.db.collection(self.PUBLIC_COMPLAINTS).document(complaint_id)
            if public_ref.get().exists:
                public_ref.update({
                    'upvotes': firestore.Increment(upvote_delta),
                    'downvotes': firestore.Increment(downvote_delta),
                    'net_votes': firestore.Increment(upvote_delta - downvote_delta)
                })
        except Exception as e:
            print(f"⚠️  Failed to update vote counts: {e}")
    
    def get_user_vote(self, complaint_id: str, roll_number: str) -> Optional[str]:
        """Get user's vote on a complaint"""
        try:
            roll_hash = self.hash_roll_number(roll_number)
            vote_id = f"{complaint_id}_{roll_hash}"
            
            doc = self.db.collection(self.VOTES).document(vote_id).get()
            if doc.exists:
                return doc.to_dict()['vote_type']
            return None
        except Exception as e:
            print(f"❌ Failed to get user vote: {e}")
            return None
    
    # =================== STATISTICS & ANALYTICS ===================
    
    def get_system_statistics(self) -> SystemStatistics:
        """Get comprehensive system statistics"""
        try:
            stats_ref = self.db.collection(self.STATISTICS).document('system')
            doc = stats_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return SystemStatistics(**data)
            
            # Calculate fresh statistics
            return self._calculate_system_statistics()
        
        except Exception as e:
            print(f"❌ Failed to get system statistics: {e}")
            return SystemStatistics()
    
    def _calculate_system_statistics(self) -> SystemStatistics:
        """Calculate system statistics from scratch"""
        try:
            # Get all complaints
            complaints_query = self.db.collection(self.COMPLAINTS).stream()
            
            stats = SystemStatistics()
            
            for doc in complaints_query:
                data = doc.to_dict()
                stats.total_complaints += 1
                
                # By visibility
                if data.get('is_public'):
                    stats.public_complaints += 1
                elif data.get('visibility_type') == 'confidential':
                    stats.confidential_complaints += 1
                else:
                    stats.private_complaints += 1
                
                # By status
                status = data.get('status', 'raised')
                if status == 'raised':
                    stats.raised_count += 1
                elif status == 'opened':
                    stats.opened_count += 1
                elif status == 'reviewed':
                    stats.reviewed_count += 1
                elif status == 'closed':
                    stats.closed_count += 1
                
                # By priority
                priority = data.get('priority_level', 'Low')
                if priority == 'Critical':
                    stats.critical_count += 1
                elif priority == 'High':
                    stats.high_count += 1
                elif priority == 'Medium':
                    stats.medium_count += 1
                elif priority == 'Low':
                    stats.low_count += 1
                
                # By category
                category = data.get('category', '')
                if category == 'academic':
                    stats.academic_count += 1
                elif category == 'hostel':
                    stats.hostel_count += 1
                elif category == 'infrastructure':
                    stats.infrastructure_count += 1
                
                # Votes
                stats.total_upvotes += data.get('upvotes', 0)
                stats.total_downvotes += data.get('downvotes', 0)
                
                # Processing time
                stats.average_processing_time += data.get('processing_time', 0)
            
            stats.processed_complaints = stats.total_complaints
            if stats.total_complaints > 0:
                stats.average_processing_time /= stats.total_complaints
            
            stats.last_updated = datetime.utcnow()
            
            # Save to cache
            self.db.collection(self.STATISTICS).document('system').set(stats.to_dict())
            
            return stats
        
        except Exception as e:
            print(f"❌ Failed to calculate statistics: {e}")
            return SystemStatistics()
    
    def get_monthly_statistics(self, year_month: str) -> MonthlyStatistics:
        """
        Get statistics for a specific month.
        
        Args:
            year_month: Format "YYYY-MM" (e.g., "2025-12")
        
        Returns:
            MonthlyStatistics object
        """
        try:
            doc = self.db.collection(f"{self.STATISTICS}/monthly/{year_month}").document('data').get()
            if doc.exists:
                return MonthlyStatistics(**doc.to_dict())
            
            # Calculate for the month
            return self._calculate_monthly_statistics(year_month)
        
        except Exception as e:
            print(f"❌ Failed to get monthly statistics: {e}")
            return MonthlyStatistics(year_month=year_month)
    
    def _calculate_monthly_statistics(self, year_month: str) -> MonthlyStatistics:
        """Calculate statistics for a specific month"""
        try:
            year, month = year_month.split('-')
            start_date = datetime(int(year), int(month), 1)
            
            if int(month) == 12:
                end_date = datetime(int(year) + 1, 1, 1)
            else:
                end_date = datetime(int(year), int(month) + 1, 1)
            
            # Query complaints in date range
            query = self.db.collection(self.COMPLAINTS).where(
                filter=FieldFilter('created_at', '>=', start_date.isoformat())
            ).where(
                filter=FieldFilter('created_at', '<', end_date.isoformat())
            )
            
            stats = MonthlyStatistics(year_month=year_month)
            
            for doc in query.stream():
                data = doc.to_dict()
                stats.total_raised += 1
                
                if data.get('status') == 'closed':
                    stats.total_closed += 1
                
                # By category
                category = data.get('category', 'infrastructure')
                stats.by_category[category] = stats.by_category.get(category, 0) + 1
                
                # By priority
                priority = data.get('priority_level', 'Low')
                stats.by_priority[priority] = stats.by_priority.get(priority, 0) + 1
                
                # By authority
                authority = data.get('assigned_authority', 'Unknown')
                stats.by_authority[authority] = stats.by_authority.get(authority, 0) + 1
                
                # By department
                dept = data.get('department', 'Unknown')
                stats.by_department[dept] = stats.by_department.get(dept, 0) + 1
            
            # Save to cache
            self.db.collection(f"{self.STATISTICS}/monthly/{year_month}").document('data').set(
                stats.to_dict()
            )
            
            return stats
        
        except Exception as e:
            print(f"❌ Failed to calculate monthly statistics: {e}")
            return MonthlyStatistics(year_month=year_month)
    
    def get_authority_statistics(self, authority_name: str) -> AuthorityStatistics:
        """Get statistics for a specific authority"""
        try:
            query = self.db.collection(self.COMPLAINTS).where(
                filter=FieldFilter('assigned_authority', '==', authority_name)
            )
            
            stats = AuthorityStatistics(authority_name=authority_name)
            
            for doc in query.stream():
                data = doc.to_dict()
                stats.total_assigned += 1
                
                status = data.get('status', 'raised')
                if status == 'closed':
                    stats.closed_count += 1
                else:
                    stats.pending_count += 1
                
                # Count critical/high pending
                priority = data.get('priority_level', 'Low')
                if priority == 'Critical':
                    stats.critical_pending += 1
                elif priority == 'High':
                    stats.high_pending += 1
            
            return stats
        
        except Exception as e:
            print(f"❌ Failed to get authority statistics: {e}")
            return AuthorityStatistics(authority_name=authority_name)
    
    # =================== EXPORT FUNCTIONALITY ===================
    
    def export_complaints_csv(
        self,
        authority_name: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export complaints to CSV format.
        
        Args:
            authority_name: Authority name
            filters: Optional filters
        
        Returns:
            CSV string
        """
        try:
            # Get complaints
            complaints, _ = self.get_complaints_by_authority(authority_name, filters, page=1, limit=1000)
            
            # Create CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'Complaint ID', 'Department', 'Category', 'Priority', 'Status',
                'Original Text', 'Rephrased Text', 'Assigned Authority',
                'Created At', 'Updated At', 'Closed At'
            ])
            
            # Write data
            for complaint in complaints:
                writer.writerow([
                    complaint.complaint_id,
                    complaint.department,
                    complaint.category,
                    complaint.priority_level,
                    complaint.status,
                    complaint.original_text,
                    complaint.rephrased_text,
                    complaint.assigned_authority,
                    complaint.created_at,
                    complaint.updated_at,
                    complaint.closed_at or 'N/A'
                ])
            
            return output.getvalue()
        
        except Exception as e:
            print(f"❌ Failed to export CSV: {e}")
            return ""
    
    # =================== DATA RETENTION & CLEANUP ===================
    
    def cleanup_old_complaints(self, retention_months: int = 6) -> int:
        """
        Archive complaints older than retention period.
        
        Args:
            retention_months: Number of months to retain
        
        Returns:
            Number of complaints archived
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_months * 30)
            
            query = self.db.collection(self.COMPLAINTS).where(
                filter=FieldFilter('created_at', '<', cutoff_date.isoformat())
            ).where(
                filter=FieldFilter('status', '==', 'closed')
            )
            
            count = 0
            for doc in query.stream():
                self.delete_complaint(doc.id)
                count += 1
            
            print(f"✅ Archived {count} old complaints")
            return count
        
        except Exception as e:
            print(f"❌ Failed to cleanup complaints: {e}")
            return 0
    
    # =================== HELPER METHODS ===================
    
    def _dict_to_complaint(self, data: Dict[str, Any]) -> Complaint:
        """Convert Firestore dict to Complaint object"""
        # Parse datetime fields
        for field in ['created_at', 'updated_at', 'opened_at', 'reviewed_at', 'closed_at']:
            if field in data and data[field]:
                data[field] = self._parse_iso_dt(data[field])
        
        return Complaint(**data)
    
    @staticmethod
    def _parse_iso_dt(s: Optional[str]) -> Optional[datetime]:
        """Parse ISO format datetime string"""
        if not s:
            return None
        try:
            if isinstance(s, datetime):
                return s
            if s.endswith('Z'):
                s = s.replace('Z', '+00:00')
            return datetime.fromisoformat(s)
        except Exception:
            return None
