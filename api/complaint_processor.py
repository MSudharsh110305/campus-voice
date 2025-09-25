import os
import sys
import time
import threading
from datetime import datetime, timezone

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add core directory to path
sys.path.insert(0, os.path.join(project_root, 'core'))

# Import core LLM modules
from config import Config
from hybrid_classifier import CampusVoiceClassifier
from llm_engine import OllamaClient

# Import API modules
from api.firebase_service import FirebaseService
from api.models import ProcessedComplaint

class ComplaintProcessor:
    """LLM-powered complaint processing engine"""
    
    def __init__(self):
        print("🤖 Initializing LLM Complaint Processor...")
        try:
            # Initialize services
            self.config = Config()
            self.firebase_service = FirebaseService()
            self.classifier = CampusVoiceClassifier(self.config)
            self.llm_client = OllamaClient(self.config)
            
            # Processing control
            self.is_running = False
            self.processing_thread = None
            
            print("✅ LLM Complaint Processor initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize processor: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def process_single_complaint(self, queued_complaint) -> bool:
        """Process a single complaint through the complete LLM pipeline"""
        complaint_id = queued_complaint.complaint_id
        
        try:
            print(f"🔄 Processing complaint {complaint_id}...")
            start_time = time.time()
            
            # =============== STEP 1: LLM Classification ===============
            classification_result = self.classifier.classify(
                complaint=queued_complaint.complaint_text,
                user_department=queued_complaint.user_department,
                upvotes=0,  # No votes yet for queued complaints
                image_data=queued_complaint.image_data,
                user_residence=queued_complaint.user_residence
            )
            
            print(f"   📂 Classification: {classification_result.category}")
            print(f"   🎯 Authority: {classification_result.final_authority}")
            print(f"   ⚡ Priority: {classification_result.priority_level}")
            
            # =============== STEP 2: LLM Rephrasing ===============
            user_context = {
                'department': queued_complaint.user_department,
                'residence': queued_complaint.user_residence,
                'email': queued_complaint.user_email
            }
            
            try:
                rephrased_complaint = self.llm_client.rephrase_complaint(
                    complaint=queued_complaint.complaint_text,
                    user_context=user_context,
                    image_data=queued_complaint.image_data,
                    classification_hint=classification_result.category
                )
                print(f"   ✍️ Complaint rephrased successfully")
            except Exception as e:
                print(f"   ⚠️ Rephrasing failed, using original: {e}")
                rephrased_complaint = queued_complaint.complaint_text
            
            # =============== STEP 3: Image Description (if applicable) ===============
            image_description = None
            if queued_complaint.image_data:
                try:
                    # Use LLM to describe the image
                    image_description = self.llm_client.describe_image(queued_complaint.image_data)
                    print(f"   🖼️ Image description generated")
                except Exception as e:
                    print(f"   ⚠️ Image description failed: {e}")
                    image_description = "Image provided but description unavailable"
            
            # =============== STEP 4: Determine Subcategory ===============
            subcategory = None
            if classification_result.category == 'academic':
                # For academic complaints, use the user's department as subcategory
                subcategory = queued_complaint.user_department
            
            # =============== STEP 5: Create Processed Complaint ===============
            processing_time = time.time() - start_time
            
            processed_complaint = ProcessedComplaint(
                complaint_id=complaint_id,
                original_complaint=queued_complaint.complaint_text,
                rephrased_complaint=rephrased_complaint,
                classification=classification_result.category,
                subcategory=subcategory,
                final_authority=classification_result.final_authority,
                routing_path=classification_result.routing_path,
                priority_level=classification_result.priority_level,
                confidence=classification_result.confidence,
                reasoning=classification_result.reasoning,
                processing_time=processing_time,
                model_used=classification_result.model_used,
                created_at=queued_complaint.created_at,
                processed_at=datetime.now(timezone.utc),
                visibility=queued_complaint.visibility,
                user_department=queued_complaint.user_department,
                user_email=queued_complaint.user_email
            )
            
            # =============== STEP 6: Save to Firebase ===============
            success = self.firebase_service.save_processed_complaint(processed_complaint)
            
            if success:
                print(f"✅ Successfully processed complaint {complaint_id}")
                print(f"   ⏱️ Total processing time: {processing_time:.2f}s")
                print(f"   🔓 Visibility: {queued_complaint.visibility}")
                return True
            else:
                print(f"❌ Failed to save processed complaint {complaint_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing complaint {complaint_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Create error fallback processing result
            try:
                error_processed = ProcessedComplaint(
                    complaint_id=complaint_id,
                    original_complaint=queued_complaint.complaint_text,
                    rephrased_complaint=queued_complaint.complaint_text,
                    classification='infrastructure',  # fallback
                    subcategory=None,
                    final_authority='Administrative Officer (AO)',
                    routing_path=['⚠️ Error in LLM processing - Routed to AO'],
                    priority_level='Medium',
                    confidence='Low',
                    reasoning=f'LLM processing error: {str(e)}',
                    processing_time=0,
                    model_used='error_fallback',
                    created_at=queued_complaint.created_at,
                    processed_at=datetime.now(timezone.utc),
                    visibility=queued_complaint.visibility,
                    user_department=queued_complaint.user_department,
                    user_email=queued_complaint.user_email
                )
                
                self.firebase_service.save_processed_complaint(error_processed)
                print(f"⚠️ Saved error fallback for complaint {complaint_id}")
                
            except Exception as fallback_error:
                print(f"💥 Critical error - could not save fallback: {fallback_error}")
            
            return False
    
    def processing_loop(self):
        """Main processing loop - continuously monitors queue"""
        print("🚀 Starting LLM processing loop...")
        print("📡 Monitoring Firebase queue for new complaints...")
        
        consecutive_empty_checks = 0
        
        while self.is_running:
            try:
                # Get next complaint from queue
                queued_complaint = self.firebase_service.get_next_queued_complaint()
                
                if queued_complaint:
                    consecutive_empty_checks = 0
                    print(f"\n📋 New complaint detected: {queued_complaint.complaint_id}")
                    print(f"   Department: {queued_complaint.user_department}")
                    print(f"   Visibility: {queued_complaint.visibility}")
                    print(f"   Text: {queued_complaint.complaint_text[:100]}...")
                    
                    # Process the complaint
                    success = self.process_single_complaint(queued_complaint)
                    
                    if success:
                        print(f"🎉 Complaint {queued_complaint.complaint_id} processed successfully!\n")
                    else:
                        print(f"⚠️ Complaint {queued_complaint.complaint_id} processing failed\n")
                else:
                    consecutive_empty_checks += 1
                    if consecutive_empty_checks % 10 == 1:  # Print every 10 empty checks
                        print("⏳ No pending complaints, waiting for new submissions...")
                    
                    time.sleep(3)  # Wait 3 seconds before checking again
                    
            except KeyboardInterrupt:
                print("\n⏹️ Processing loop stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error in processing loop: {str(e)}")
                time.sleep(5)  # Wait before retrying on error
    
    def start_background_processing(self):
        """Start processing in background thread"""
        if not self.is_running:
            self.is_running = True
            self.processing_thread = threading.Thread(target=self.processing_loop, daemon=True)
            self.processing_thread.start()
            print("🎬 Background LLM processing started")
        else:
            print("⚠️ Processing already running")
    
    def stop_processing(self):
        """Stop background processing"""
        if self.is_running:
            self.is_running = False
            if self.processing_thread:
                self.processing_thread.join(timeout=5)
            print("⏹️ LLM processing stopped")
    
    def run_blocking(self):
        """Run processor in blocking mode (for standalone execution)"""
        self.is_running = True
        try:
            self.processing_loop()
        except KeyboardInterrupt:
            print("\n🛑 Processor stopped by user")
        finally:
            self.is_running = False

# =============== STANDALONE EXECUTION ===============
if __name__ == '__main__':
    print("🤖 Campus Grievance Portal - LLM Complaint Processor")
    print("=" * 60)
    print("📝 This service processes complaints using AI/LLM technology")
    print("🔄 Monitoring Firebase queue for new complaints...")
    print("⏹️ Press Ctrl+C to stop")
    print("=" * 60)
    
    try:
        processor = ComplaintProcessor()
        processor.run_blocking()
    except KeyboardInterrupt:
        print("\n🛑 LLM Processor stopped by user")
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        import traceback
        traceback.print_exc()
