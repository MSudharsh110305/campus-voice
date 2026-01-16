"""
Complaint Processor - CampusVoice Complaint System
Version: 5.0.0 - Production Ready

Simple orchestration layer for complaint processing.
Coordinates LLM engine, Firebase service, and image uploads.

Changes from v4.0:
- ✅ FIXED: Version updated to 5.0.0
- ✅ FIXED: All datetime instances use timezone.utc
- ✅ FIXED: Consistent with firebase_service v5.0 and intelligent_llm_engine v5.0
- ✅ FIXED: Improved error handling and logging
- ✅ All orchestration flows tested and production-ready
"""

import os
import sys
import time
import uuid
from typing import Optional, List, Tuple, Any
from datetime import datetime, timezone

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import core modules
from core.config import get_config

# Import API modules
from api.intelligent_llm_engine import IntelligentLLMEngine
from api.firebase_service import FirebaseService
from api.models import ComplaintSubmission, Complaint


class ComplaintProcessor:
    """
    Simple orchestration layer for complaint processing.
    
    Coordinates:
    - LLM engine (categorization, routing, priority)
    - Firebase service (storage)
    - Image uploads
    """
    
    def __init__(self):
        """Initialize the complaint processor."""
        print("🤖 Initializing Complaint Processor...")
        
        try:
            # Get configuration
            self.config = get_config()
            
            # Initialize services
            self.firebase_service = FirebaseService()
            self.llm_engine = IntelligentLLMEngine()
            
            print("✅ Complaint Processor ready")
            print(f"   🚀 LLM: {'Groq' if self.llm_engine.groq_available else 'Rule-based'}")
            print(f"   🔥 Firebase: Connected")
        
        except Exception as e:
            print(f"❌ Failed to initialize processor: {e}")
            raise
    
    def process_complaint(
        self,
        submission: ComplaintSubmission,
        image_files: Optional[List[Any]] = None,
        image_filenames: Optional[List[str]] = None
    ) -> Tuple[bool, str, Optional[Complaint]]:
        """
        Process a complaint submission.
        
        This is the main entry point for complaint processing.
        
        Args:
            submission: ComplaintSubmission object
            image_files: Optional list of image files (file objects or bytes)
            image_filenames: Optional list of image filenames
        
        Returns:
            Tuple of (success: bool, message: str, complaint: Optional[Complaint])
        """
        complaint_id = None
        
        try:
            # Generate unique complaint ID
            complaint_id = self._generate_complaint_id()
            
            print(f"\n🔄 Processing complaint: {complaint_id}")
            print(f"   📝 Text: {submission.complaint_text[:80]}...")
            print(f"   👤 Roll: {submission.roll_number}")
            print(f"   🏫 Dept: {submission.department}")
            print(f"   🏠 Residence: {submission.residence}")
            print(f"   ⚧ Gender: {submission.gender}")
            print(f"   👁️  Public: {submission.is_public}")
            
            if image_files:
                print(f"   🖼️  Images: {len(image_files)} attached")
            
            start_time = time.time()
            
            # =================== STEP 1: LLM PROCESSING ===================
            print("   🧠 Step 1: LLM Processing...")
            
            # LLM engine does everything:
            # - Categorization
            # - Rephrasing
            # - Visibility determination
            # - Authority routing (via AuthorityMapper)
            # - Priority scoring (via PriorityScorer)
            # - Image detection
            # - Abusive language detection
            complaint = self.llm_engine.process_complaint(submission, complaint_id)
            
            print(f"   ✅ LLM Processing complete")
            print(f"   ✍️  Rephrased: {complaint.rephrased_text[:60]}...")
            print(f"   📂 Category: {complaint.category}")
            print(f"   🔓 Visibility: {complaint.visibility_type}")
            print(f"   🎯 Authority: {complaint.assigned_authority}")
            print(f"   ⚡ Priority: {complaint.priority_level} ({complaint.priority_score:.1f})")
            print(f"   🧠 Model: {complaint.llm_model_used}")
            
            if complaint.contains_abusive_language:
                print(f"   ⚠️  Abusive language detected and cleaned")
            
            # =================== STEP 2: SAVE TO FIREBASE ===================
            print("   💾 Step 2: Saving to Firebase...")
            
            success = self.firebase_service.create_complaint(complaint)
            if not success:
                return (
                    False,
                    "Failed to save complaint to database",
                    None
                )
            
            print(f"   ✅ Saved to Firebase")
            
            # =================== STEP 3: UPLOAD IMAGES ===================
            if image_files and image_filenames:
                print(f"   📸 Step 3: Uploading {len(image_files)} images...")
                
                image_urls = self._upload_images(
                    complaint_id,
                    image_files,
                    image_filenames
                )
                
                if image_urls:
                    # Update complaint with image URLs
                    complaint.image_urls = image_urls
                    self.firebase_service.update_complaint(
                        complaint_id,
                        {'image_urls': image_urls}
                    )
                    print(f"   ✅ Uploaded {len(image_urls)} images")
                else:
                    print(f"   ⚠️  Image upload failed (complaint still saved)")
            else:
                print("   ℹ️  Step 3: No images to upload")
            
            # =================== COMPLETE ===================
            processing_time = time.time() - start_time
            print(f"   ✅ Processing complete in {processing_time:.2f}s")
            print(f"   🆔 Complaint ID: {complaint_id}")
            
            return (
                True,
                f"Complaint processed successfully: {complaint_id}",
                complaint
            )
        
        except Exception as e:
            print(f"   ❌ Error processing complaint: {str(e)}")
            
            # Try to save error fallback
            try:
                if complaint_id:
                    self._save_error_fallback(submission, complaint_id, str(e))
                    return (
                        False,
                        f"Processing error (fallback saved): {str(e)}",
                        None
                    )
            except Exception as fallback_error:
                print(f"   💥 Critical: Could not save error fallback: {fallback_error}")
            
            return (
                False,
                f"Processing error: {str(e)}",
                None
            )
    
    def _generate_complaint_id(self) -> str:
        """Generate unique complaint ID."""
        timestamp = int(time.time() * 1000)
        unique_id = str(uuid.uuid4())[:8]
        return f"complaint_{timestamp}_{unique_id}"
    
    def _upload_images(
        self,
        complaint_id: str,
        image_files: List[Any],
        image_filenames: List[str]
    ) -> List[str]:
        """
        Upload images to Firebase Storage.
        
        Args:
            complaint_id: Complaint identifier
            image_files: List of file objects or bytes
            image_filenames: List of filenames
        
        Returns:
            List of public URLs
        """
        try:
            image_urls = self.firebase_service.upload_multiple_images(
                complaint_id,
                image_files,
                image_filenames
            )
            return image_urls
        
        except Exception as e:
            print(f"   ❌ Failed to upload images: {e}")
            return []
    
    def _save_error_fallback(
        self,
        submission: ComplaintSubmission,
        complaint_id: str,
        error_message: str
    ):
        """
        Save error fallback complaint when processing fails.
        
        Args:
            submission: Original submission
            complaint_id: Generated complaint ID
            error_message: Error message string
        """
        try:
            # Create minimal complaint with error info
            roll_hash = self.firebase_service.hash_roll_number(submission.roll_number)
            
            error_complaint = Complaint(
                complaint_id=complaint_id,
                roll_number_hash=roll_hash,
                department=submission.department,
                gender=submission.gender,
                residence=submission.residence,
                original_text=submission.complaint_text,
                rephrased_text=f"[ERROR] Complaint processing failed. Please review manually.",
                category='infrastructure',  # Default
                assigned_authority='Administrative Officer',  # Default
                routing_path=['Administrative Officer'],
                routing_reasoning=f'Error fallback: {error_message[:200]}',
                hidden_from=[],
                bypass_applied=False,
                escalated_to=None,
                priority_level='Medium',
                priority_score=50.0,
                priority_breakdown=['Error fallback - default priority'],
                priority_emoji='⚠️',
                status='raised',
                visibility_type='private',  # Default to private on error
                is_public=False,
                requires_image=False,
                image_requirement_reason='N/A',
                is_mandatory_image=False,
                image_urls=[],
                upvotes=0,
                downvotes=0,
                net_votes=0,
                created_at=datetime.now(timezone.utc),  # ✅ FIXED: timezone.utc
                updated_at=datetime.now(timezone.utc),  # ✅ FIXED: timezone.utc
                opened_at=None,
                reviewed_at=None,
                closed_at=None,
                status_history=[],
                processing_time=0,
                llm_model_used='error_fallback',
                llm_confidence='Low',
                contains_abusive_language=False,
                language_issues=None
            )
            
            # Save to Firebase
            self.firebase_service.create_complaint(error_complaint)
            print(f"   ⚠️  Error fallback saved: {complaint_id}")
        
        except Exception as e:
            print(f"   💥 Could not save error fallback: {e}")
    
    # =================== BATCH PROCESSING (OPTIONAL) ===================
    
    def process_multiple_complaints(
        self,
        submissions: List[ComplaintSubmission]
    ) -> List[Tuple[bool, str, Optional[Complaint]]]:
        """
        Process multiple complaints in sequence.
        
        Args:
            submissions: List of ComplaintSubmission objects
        
        Returns:
            List of (success, message, complaint) tuples
        """
        results = []
        
        print(f"\n📦 Batch processing {len(submissions)} complaints...")
        
        for idx, submission in enumerate(submissions, 1):
            print(f"\n[{idx}/{len(submissions)}]")
            result = self.process_complaint(submission)
            results.append(result)
        
        # Summary
        successful = sum(1 for r in results if r[0])
        print(f"\n✅ Batch complete: {successful}/{len(submissions)} successful")
        
        return results
    
    # =================== UTILITY METHODS ===================
    
    def get_complaint(self, complaint_id: str) -> Optional[Complaint]:
        """
        Get a complaint by ID.
        
        Args:
            complaint_id: Complaint identifier
        
        Returns:
            Complaint object or None
        """
        return self.firebase_service.get_complaint(complaint_id)
    
    def update_complaint_status(
        self,
        complaint_id: str,
        new_status: str,
        updated_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Update complaint status.
        
        Args:
            complaint_id: Complaint identifier
            new_status: New status (raised/opened/reviewed/closed)
            updated_by: Authority identifier
            notes: Optional notes
        
        Returns:
            Success status
        """
        return self.firebase_service.update_status(
            complaint_id,
            new_status,
            updated_by,
            notes
        )
    
    def get_processing_statistics(self) -> dict:
        """Get processing statistics."""
        stats = self.firebase_service.get_system_statistics()
        
        return {
            'total_complaints': stats.total_complaints,
            'by_status': {
                'raised': stats.raised_count,
                'opened': stats.opened_count,
                'reviewed': stats.reviewed_count,
                'closed': stats.closed_count
            },
            'by_priority': {
                'critical': stats.critical_count,
                'high': stats.high_count,
                'medium': stats.medium_count,
                'low': stats.low_count
            },
            'by_category': {
                'academic': stats.academic_count,
                'hostel': stats.hostel_count,
                'infrastructure': stats.infrastructure_count
            },
            'average_processing_time': stats.average_processing_time
        }


# =================== STANDALONE TESTING ===================

if __name__ == '__main__':
    """Standalone testing mode."""
    print("=" * 70)
    print("🤖 CAMPUSVOICE - COMPLAINT PROCESSOR TEST")
    print("=" * 70)
    print()
    
    try:
        # Initialize processor
        processor = ComplaintProcessor()
        
        # Create test submission
        test_submission = ComplaintSubmission(
            roll_number="21CS001",
            department="Computer Science & Engineering",
            gender="male",
            residence="Hostel A",
            complaint_text="The WiFi in hostel is not working properly. Speed is very slow and keeps disconnecting.",
            is_public=True
        )
        
        print("\n📝 Test Submission:")
        print(f"   Roll: {test_submission.roll_number}")
        print(f"   Dept: {test_submission.department}")
        print(f"   Text: {test_submission.complaint_text}")
        print()
        
        # Process complaint
        success, message, complaint = processor.process_complaint(test_submission)
        
        print("\n" + "=" * 70)
        if success and complaint:
            print("✅ TEST PASSED")
            print(f"\n🆔 Complaint ID: {complaint.complaint_id}")
            print(f"📂 Category: {complaint.category}")
            print(f"🎯 Authority: {complaint.assigned_authority}")
            print(f"⚡ Priority: {complaint.priority_level} ({complaint.priority_score:.1f})")
            print(f"✍️  Rephrased: {complaint.rephrased_text[:100]}...")
        else:
            print("❌ TEST FAILED")
            print(f"   Message: {message}")
        
        print("=" * 70)
    
    except KeyboardInterrupt:
        print("\n🛑 Test stopped by user")
    
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
