import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
import uuid
import time

from api.models import (
    QueuedComplaint, LLMProcessingResult, PublicComplaint, 
    PrivateComplaint, AnonymousComplaintSubmission
)

class FirebaseService:
    """Complete Firebase service for pseudo-anonymous complaint processing"""
    
    def __init__(self, credentials_path: str = 'firebase-key.json'):
        # Initialize Firebase Admin SDK
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
                print("🔥 Firebase initialized successfully")
            except Exception as e:
                print(f"❌ Firebase initialization failed: {e}")
                raise
        
        self.db = firestore.client()
        
        # Collection names
        self.QUEUED_COMPLAINTS = 'queued_complaints'
        self.PROCESSED_COMPLAINTS = 'processed_complaints'
        self.PUBLIC_COMPLAINTS = 'public_complaints'
        self.PRIVATE_COMPLAINTS = 'private_complaints'
        self.COMPLAINT_VOTES = 'complaint_votes'
        
        print("📊 Firebase collections ready for pseudo-anonymous processing")
    
    # =================== QUEUE OPERATIONS ===================
    
    def submit_raw_complaint(self, submission: AnonymousComplaintSubmission) -> Tuple[str, int]:
        """Submit raw complaint to queue for LLM processing"""
        try:
            # Generate unique complaint ID
            complaint_id = f"complaint_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
            
            # Create queued complaint
            queued_complaint = QueuedComplaint(
                complaint_id=complaint_id,
                original_complaint=submission.complaint_text,
                user_department=submission.user_department,
                user_residence=submission.user_residence,
                user_email=submission.user_email,
                image_data=submission.image_data,
                created_at=datetime.now(timezone.utc),
                status='pending'
            )
            
            # Add to Firebase queue
            doc_ref = self.db.collection(self.QUEUED_COMPLAINTS).document(complaint_id)
            doc_ref.set(queued_complaint.to_dict())
            
            # Get queue position
            queue_position = self._get_current_queue_position()
            
            # Update queue position
            doc_ref.update({'queue_position': queue_position})
            
            print(f"📝 Raw complaint queued: {complaint_id} (position: {queue_position})")
            return complaint_id, queue_position
            
        except Exception as e:
            print(f"❌ Failed to queue complaint: {e}")
            raise
    
    def get_next_queued_complaint(self) -> Optional[QueuedComplaint]:
        """Get next raw complaint from queue for LLM processing"""
        try:
            # Get oldest pending complaint
            docs = list(
                self.db.collection(self.QUEUED_COMPLAINTS)
                .where('status', '==', 'pending')
                .limit(5)  # Get small batch to avoid timeout
                .stream()
            )
            
            if not docs:
                return None
            
            # Sort by created_at to get oldest first
            sorted_docs = sorted(docs, key=lambda d: d.to_dict().get('created_at', ''))
            doc = sorted_docs[0]
            data = doc.to_dict()
            
            # Mark as processing
            doc.reference.update({
                'status': 'processing',
                'processing_started_at': datetime.now(timezone.utc)
            })
            
            # Convert to model
            queued_complaint = QueuedComplaint(
                complaint_id=data['complaint_id'],
                original_complaint=data['original_complaint'],
                user_department=data['user_department'],
                user_residence=data.get('user_residence'),
                user_email=data.get('user_email'),
                image_data=data.get('image_data'),
                created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                status='processing',
                queue_position=data.get('queue_position', 0)
            )
            
            print(f"🔄 Retrieved raw complaint for LLM processing: {queued_complaint.complaint_id}")
            return queued_complaint
            
        except Exception as e:
            print(f"❌ Failed to get queued complaint: {e}")
            return None
    
    def _get_current_queue_position(self) -> int:
        """Calculate current queue position"""
        try:
            count = len(list(
                self.db.collection(self.QUEUED_COMPLAINTS)
                .where('status', '==', 'pending')
                .stream()
            ))
            return count + 1
        except:
            return 1
    
    # =================== PROCESSING OPERATIONS ===================
    
    def save_llm_processed_complaint(self, llm_result: LLMProcessingResult) -> bool:
        """Save LLM-processed complaint to appropriate collections and delete from queue"""
        try:
            # 1. Save to main processed complaints collection
            processed_doc = self.db.collection(self.PROCESSED_COMPLAINTS).document(llm_result.complaint_id)
            processed_doc.set(llm_result.to_dict())
            
            # 2. Save to visibility-specific collection
            if llm_result.llm_determined_visibility == 'public':
                self._save_to_public_collection(llm_result)
            else:
                self._save_to_private_collection(llm_result)
            
            # 3. Delete from queue (critical step)
            self._delete_from_queue(llm_result.complaint_id)
            
            print(f"✅ LLM-processed complaint saved and queue cleaned: {llm_result.complaint_id}")
            print(f"   🔓 Visibility: {llm_result.llm_determined_visibility}")
            print(f"   📂 Category: {llm_result.classification}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to save processed complaint: {e}")
            return False
    
    def _save_to_public_collection(self, llm_result: LLMProcessingResult):
        """Save to public complaints collection for community voting"""
        try:
            public_complaint = PublicComplaint(
                complaint_id=llm_result.complaint_id,
                rephrased_complaint=llm_result.rephrased_complaint,
                classification=llm_result.classification,
                final_authority=llm_result.final_authority,
                priority_level=llm_result.priority_level,
                department=llm_result.user_department,
                created_at=llm_result.created_at
            )
            
            self.db.collection(self.PUBLIC_COMPLAINTS).document(llm_result.complaint_id).set(
                public_complaint.to_dict()
            )
            
            print(f"🔓 Public complaint available for voting: {llm_result.complaint_id}")
            
        except Exception as e:
            print(f"❌ Failed to save public complaint: {e}")
    
    def _save_to_private_collection(self, llm_result: LLMProcessingResult):
        """Save to private complaints collection"""
        try:
            private_complaint = PrivateComplaint(
                complaint_id=llm_result.complaint_id,
                original_complaint=llm_result.original_complaint,
                rephrased_complaint=llm_result.rephrased_complaint,
                classification=llm_result.classification,
                final_authority=llm_result.final_authority,
                llm_determined_visibility=llm_result.llm_determined_visibility,
                user_email=llm_result.user_email,
                created_at=llm_result.created_at
            )
            
            self.db.collection(self.PRIVATE_COMPLAINTS).document(llm_result.complaint_id).set(
                private_complaint.to_dict()
            )
            
            print(f"🔒 Private complaint secured: {llm_result.complaint_id}")
            
        except Exception as e:
            print(f"❌ Failed to save private complaint: {e}")
    
    def _delete_from_queue(self, complaint_id: str):
        """Delete processed complaint from queue"""
        try:
            self.db.collection(self.QUEUED_COMPLAINTS).document(complaint_id).delete()
            print(f"🗑️ Complaint removed from queue: {complaint_id}")
        except Exception as e:
            print(f"❌ Failed to delete from queue: {e}")
    
    # =================== RETRIEVAL OPERATIONS ===================
    
    def get_complaint_status(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """Get complaint status from any collection"""
        try:
            # Check if still in queue
            queue_doc = self.db.collection(self.QUEUED_COMPLAINTS).document(complaint_id).get()
            if queue_doc.exists:
                data = queue_doc.to_dict()
                data['location'] = 'queue'
                data['processing_stage'] = 'awaiting_llm_processing'
                return data
            
            # Check processed complaints
            processed_doc = self.db.collection(self.PROCESSED_COMPLAINTS).document(complaint_id).get()
            if processed_doc.exists:
                data = processed_doc.to_dict()
                
                # Add visibility-specific information
                if data.get('llm_determined_visibility') == 'public':
                    public_doc = self.db.collection(self.PUBLIC_COMPLAINTS).document(complaint_id).get()
                    if public_doc.exists:
                        public_data = public_doc.to_dict()
                        data['upvotes'] = public_data.get('upvotes', 0)
                        data['downvotes'] = public_data.get('downvotes', 0)
                        data['location'] = 'public'
                        data['processing_stage'] = 'public_voting_available'
                else:
                    data['location'] = 'private'
                    data['processing_stage'] = 'privately_processed'
                
                return data
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get complaint status: {e}")
            return None
    
    def get_public_complaints(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get public complaints available for voting"""
        try:
            query = self.db.collection(self.PUBLIC_COMPLAINTS).limit(limit)
            
            if category:
                query = query.where('classification', '==', category)
            
            complaints = []
            for doc in query.stream():
                data = doc.to_dict()
                complaints.append(data)
            
            # Sort by creation time (most recent first)
            complaints.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return complaints
            
        except Exception as e:
            print(f"❌ Failed to get public complaints: {e}")
            return []
    
    def get_complaints_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all processed complaints by category"""
        try:
            complaints = []
            
            # Get from processed complaints collection
            docs = (self.db.collection(self.PROCESSED_COMPLAINTS)
                   .where('classification', '==', category)
                   .limit(limit)
                   .stream())
            
            for doc in docs:
                data = doc.to_dict()
                complaints.append(data)
            
            return complaints
            
        except Exception as e:
            print(f"❌ Failed to get complaints by category: {e}")
            return []
    
    # =================== VOTING OPERATIONS ===================
    
    def vote_on_public_complaint(self, complaint_id: str, user_id: str, vote_type: str) -> Dict[str, Any]:
        """Handle voting on public complaints"""
        try:
            # Verify complaint is public
            public_doc = self.db.collection(self.PUBLIC_COMPLAINTS).document(complaint_id).get()
            if not public_doc.exists:
                return {'success': False, 'message': 'Complaint not found or not public'}
            
            # Handle voting logic
            vote_id = f"{complaint_id}_{user_id}"
            vote_doc = self.db.collection(self.COMPLAINT_VOTES).document(vote_id).get()
            
            if vote_doc.exists:
                old_vote = vote_doc.to_dict()['vote_type']
                if old_vote == vote_type:
                    return {'success': False, 'message': 'Already voted with same type'}
                
                # Update existing vote
                vote_doc.reference.update({
                    'vote_type': vote_type,
                    'updated_at': datetime.now(timezone.utc)
                })
                
                # Update complaint counts
                if old_vote == 'upvote' and vote_type == 'downvote':
                    public_doc.reference.update({
                        'upvotes': firestore.Increment(-1),
                        'downvotes': firestore.Increment(1)
                    })
                elif old_vote == 'downvote' and vote_type == 'upvote':
                    public_doc.reference.update({
                        'upvotes': firestore.Increment(1),
                        'downvotes': firestore.Increment(-1)
                    })
            else:
                # New vote
                vote_data = {
                    'complaint_id': complaint_id,
                    'user_id': user_id,
                    'vote_type': vote_type,
                    'created_at': datetime.now(timezone.utc)
                }
                
                self.db.collection(self.COMPLAINT_VOTES).document(vote_id).set(vote_data)
                
                # Update complaint counts
                if vote_type == 'upvote':
                    public_doc.reference.update({'upvotes': firestore.Increment(1)})
                else:
                    public_doc.reference.update({'downvotes': firestore.Increment(1)})
            
            return {'success': True, 'message': 'Vote recorded successfully'}
            
        except Exception as e:
            print(f"❌ Failed to record vote: {e}")
            return {'success': False, 'message': f'Voting error: {str(e)}'}
    
    # =================== STATISTICS ===================
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            # Count documents in each collection
            queue_count = len(list(self.db.collection(self.QUEUED_COMPLAINTS).stream()))
            processed_count = len(list(self.db.collection(self.PROCESSED_COMPLAINTS).stream()))
            public_count = len(list(self.db.collection(self.PUBLIC_COMPLAINTS).stream()))
            private_count = len(list(self.db.collection(self.PRIVATE_COMPLAINTS).stream()))
            
            # Count by processing status
            pending_count = len(list(
                self.db.collection(self.QUEUED_COMPLAINTS)
                .where('status', '==', 'pending')
                .stream()
            ))
            
            processing_count = len(list(
                self.db.collection(self.QUEUED_COMPLAINTS)
                .where('status', '==', 'processing')
                .stream()
            ))
            
            return {
                'queue_status': {
                    'total_queued': queue_count,
                    'pending_processing': pending_count,
                    'currently_processing': processing_count
                },
                'processed_complaints': {
                    'total_processed': processed_count,
                    'public_complaints': public_count,
                    'private_complaints': private_count
                },
                'system_health': {
                    'collections_active': 5,
                    'auto_cleanup_enabled': True,
                    'llm_processing_active': True
                }
            }
            
        except Exception as e:
            print(f"❌ Failed to get statistics: {e}")
            return {'error': str(e)}
