import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import json
from typing import Dict, Any, Optional, List
import os

class FirebaseService:
    def __init__(self, credentials_path: str = 'firebase-key.json'):
        """Initialize Firebase service with real connection"""
        print("🔥 Initializing Real Firebase Service...")
        
        # Check if Firebase app already initialized
        if not firebase_admin._apps:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Firebase credentials file not found: {credentials_path}")
            
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully")
        
        self.db = firestore.client()
        self.complaints_collection = 'complaints'
        self.votes_collection = 'complaint_votes'
        
        # Test connection
        try:
            # Simple test to verify connection
            self.db.collection('test').limit(1).get()
            print("✅ Firebase connection verified")
        except Exception as e:
            print(f"❌ Firebase connection failed: {e}")
            raise
    
    def save_complaint(self, complaint_data: Dict[str, Any]) -> str:
        """Save complaint to Firebase and return document ID"""
        try:
            # Add metadata
            complaint_data.update({
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'status': 'pending',
                'upvotes': 0,
                'downvotes': 0
            })
            
            # Add to Firestore
            doc_ref = self.db.collection(self.complaints_collection).add(complaint_data)
            complaint_id = doc_ref[1].id
            
            print(f"✅ Firebase: Saved complaint {complaint_id}")
            return complaint_id
            
        except Exception as e:
            print(f"❌ Firebase save error: {e}")
            raise
    
    def update_complaint_processing(self, complaint_id: str, processing_result: Dict[str, Any]):
        """Update complaint with LLM processing results"""
        try:
            update_data = {
                'status': 'processed',
                'classification': processing_result.get('category'),
                'final_authority': processing_result.get('final_authority'),
                'routing_path': processing_result.get('routing_path', []),
                'priority_level': processing_result.get('priority_level'),
                'confidence': processing_result.get('confidence'),
                'reasoning': processing_result.get('reasoning'),
                'rephrased_complaint': processing_result.get('rephrased_complaint'),
                'processing_time': processing_result.get('processing_time'),
                'model_used': processing_result.get('model_used'),
                'processed_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection(self.complaints_collection).document(complaint_id).update(update_data)
            print(f"✅ Firebase: Updated complaint {complaint_id} processing")
            
        except Exception as e:
            print(f"❌ Firebase update error: {e}")
            raise
    
    def get_complaint_status(self, complaint_id: str) -> Optional[Dict[str, Any]]:
        """Get complaint status and details"""
        try:
            doc = self.db.collection(self.complaints_collection).document(complaint_id).get()
            
            if doc.exists:
                data = doc.to_dict()
                data['complaint_id'] = doc.id
                
                # Convert timestamps to strings for JSON serialization
                for key in ['created_at', 'updated_at', 'processed_at']:
                    if key in data and data[key]:
                        data[key] = data[key].isoformat() if hasattr(data[key], 'isoformat') else str(data[key])
                
                return data
            
            return None
            
        except Exception as e:
            print(f"❌ Firebase get error: {e}")
            raise
    
    def get_public_complaints(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get public complaints for upvoting/downvoting"""
        try:
            query = self.db.collection(self.complaints_collection).where('privacy_level', '==', 'public')
            
            if category:
                query = query.where('classification', '==', category)
            
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
            
            complaints = []
            for doc in query.stream():
                data = doc.to_dict()
                data['complaint_id'] = doc.id
                
                # Remove sensitive information
                data.pop('user_email', None)
                data.pop('user_phone', None)
                
                # Convert timestamps
                for key in ['created_at', 'updated_at', 'processed_at']:
                    if key in data and data[key]:
                        data[key] = data[key].isoformat() if hasattr(data[key], 'isoformat') else str(data[key])
                
                complaints.append(data)
            
            print(f"✅ Firebase: Retrieved {len(complaints)} public complaints")
            return complaints
            
        except Exception as e:
            print(f"❌ Firebase query error: {e}")
            raise
    
    def vote_complaint(self, complaint_id: str, user_id: str, vote_type: str) -> Dict[str, Any]:
        """Handle upvote/downvote for public complaints"""
        try:
            complaint_ref = self.db.collection(self.complaints_collection).document(complaint_id)
            complaint_doc = complaint_ref.get()
            
            if not complaint_doc.exists:
                return {'success': False, 'message': 'Complaint not found'}
            
            complaint_data = complaint_doc.to_dict()
            if complaint_data.get('privacy_level') != 'public':
                return {'success': False, 'message': 'Cannot vote on non-public complaints'}
            
            # Check existing vote
            vote_ref = self.db.collection(self.votes_collection).document(f"{complaint_id}_{user_id}")
            existing_vote = vote_ref.get()
            
            if existing_vote.exists:
                old_vote = existing_vote.to_dict()['vote_type']
                if old_vote == vote_type:
                    return {'success': False, 'message': 'Already voted'}
                
                # Update existing vote
                vote_ref.update({
                    'vote_type': vote_type, 
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
                
                # Update complaint counts
                if old_vote == 'upvote' and vote_type == 'downvote':
                    complaint_ref.update({
                        'upvotes': firestore.Increment(-1),
                        'downvotes': firestore.Increment(1)
                    })
                elif old_vote == 'downvote' and vote_type == 'upvote':
                    complaint_ref.update({
                        'upvotes': firestore.Increment(1),
                        'downvotes': firestore.Increment(-1)
                    })
            else:
                # New vote
                vote_ref.set({
                    'complaint_id': complaint_id,
                    'user_id': user_id,
                    'vote_type': vote_type,
                    'created_at': firestore.SERVER_TIMESTAMP
                })
                
                # Update complaint counts
                if vote_type == 'upvote':
                    complaint_ref.update({'upvotes': firestore.Increment(1)})
                else:
                    complaint_ref.update({'downvotes': firestore.Increment(1)})
            
            print(f"✅ Firebase: Vote recorded for complaint {complaint_id}")
            return {'success': True, 'message': 'Vote recorded successfully'}
            
        except Exception as e:
            print(f"❌ Firebase vote error: {e}")
            return {'success': False, 'message': f'Vote failed: {str(e)}'}
