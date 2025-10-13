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

# Import core modules
from config import Config
from hybrid_classifier import CampusVoiceClassifier
from authority_mapper import AuthorityMapper
from priority_scorer import PriorityScorer
from intelligent_llm_engine import IntelligentLLMEngine

# Import API modules
from api.firebase_service import FirebaseService
from api.models import LLMProcessingResult

class IntelligentComplaintProcessor:
    """LLM-driven complaint processor with intelligent rephrasing and visibility detection"""
    
    def __init__(self):
        print("🤖 Initializing Intelligent Complaint Processor...")
        try:
            # Initialize services
            self.config = Config()
            self.firebase_service = FirebaseService()
            self.llm_engine = IntelligentLLMEngine(self.config)
            self.authority_mapper = AuthorityMapper(self.config)
            self.priority_scorer = PriorityScorer(self.config)
            
            # Processing control
            self.is_running = False
            self.processing_thread = None
            
            print("✅ Intelligent Complaint Processor ready")
            
        except Exception as e:
            print(f"❌ Failed to initialize processor: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def process_queued_complaint(self, queued_complaint) -> bool:
        """Process raw complaint with complete LLM intelligence"""
        complaint_id = queued_complaint.complaint_id
        
        try:
            print(f"\n🔄 Processing raw complaint: {complaint_id}")
            print(f"   📝 Original: {queued_complaint.original_complaint[:80]}...")
            print(f"   🏫 Department: {queued_complaint.user_department}")
            
            start_time = time.time()
            
            # =============== STEP 1: LLM Complete Processing ===============
            user_context = {
                'department': queued_complaint.user_department,
                'residence': queued_complaint.user_residence,
                'email': queued_complaint.user_email
            }
            
            # LLM processes everything: rephrasing, visibility, classification
            llm_result = self.llm_engine.process_complaint_complete(
                queued_complaint.original_complaint, 
                user_context
            )
            
            print(f"   ✍️ Rephrased: {llm_result['rephrased_complaint'][:60]}...")
            print(f"   🔓 LLM Visibility: {llm_result['visibility']}")
            print(f"   📂 LLM Category: {llm_result['category']}")
            
            # =============== STEP 2: Authority Mapping ===============
            routing = self.authority_mapper.route_complaint(
                category=llm_result['category'],
                user_department=queued_complaint.user_department,
                needs_bypass=False,  # Could be enhanced with LLM detection
                mentioned_authority='none'
            )
            
            print(f"   🎯 Authority: {routing['final_authority']}")
            
            # =============== STEP 3: Priority Scoring ===============
            priority = self.priority_scorer.calculate_priority(
                llm_result['rephrased_complaint'], 
                upvotes=0
            )
            
            print(f"   ⚡ Priority: {priority['level']}")
            
            # =============== STEP 4: Create Processing Result ===============
            processing_time = time.time() - start_time
            
            llm_processing_result = LLMProcessingResult(
                complaint_id=complaint_id,
                original_complaint=queued_complaint.original_complaint,
                rephrased_complaint=llm_result['rephrased_complaint'],
                llm_determined_visibility=llm_result['visibility'],
                classification=llm_result['category'],
                subcategory=queued_complaint.user_department if llm_result['category'] == 'academic' else None,
                final_authority=routing['final_authority'],
                routing_path=routing['routing_path'],
                priority_level=priority['level'],
                confidence=llm_result.get('confidence', 'Medium'),
                reasoning=llm_result.get('reasoning', 'LLM-based processing'),
                processing_time=processing_time,
                model_used=llm_result.get('model_used', 'intelligent_llm_engine'),
                created_at=queued_complaint.created_at,
                processed_at=datetime.now(timezone.utc),
                user_department=queued_complaint.user_department,
                user_email=queued_complaint.user_email
            )
            
            # =============== STEP 5: Save and Clean Queue ===============
            success = self.firebase_service.save_llm_processed_complaint(llm_processing_result)
            
            if success:
                print(f"✅ Successfully processed and saved: {complaint_id}")
                print(f"   ⏱️ Processing time: {processing_time:.2f}s")
                print(f"   🧠 Model: {llm_result.get('model_used', 'N/A')}")
                return True
            else:
                print(f"❌ Failed to save processed complaint: {complaint_id}")
                return False
                
        except Exception as e:
            print(f"❌ Error processing complaint {complaint_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Try to save error fallback (but still clean queue)
            try:
                self._save_error_fallback(queued_complaint, str(e))
            except Exception as fallback_error:
                print(f"💥 Critical: Could not save error fallback: {fallback_error}")
            
            return False
    
    def _save_error_fallback(self, queued_complaint, error_message: str):
        """Save error fallback and clean queue"""
        
        error_result = LLMProcessingResult(
            complaint_id=queued_complaint.complaint_id,
            original_complaint=queued_complaint.original_complaint,
            rephrased_complaint=queued_complaint.original_complaint,  # Use original
            llm_determined_visibility='public',  # Safe default
            classification='infrastructure',  # Safe default
            subcategory=None,
            final_authority='Administrative Officer (AO)',
            routing_path=['⚠️ Error Processing - Routed to Admin'],
            priority_level='Medium',
            confidence='Low',
            reasoning=f'Error fallback: {error_message}',
            processing_time=0,
            model_used='error_fallback',
            created_at=queued_complaint.created_at,
            processed_at=datetime.now(timezone.utc),
            user_department=queued_complaint.user_department,
            user_email=queued_complaint.user_email
        )
        
        self.firebase_service.save_llm_processed_complaint(error_result)
        print(f"⚠️ Error fallback saved for: {queued_complaint.complaint_id}")
    
    def processing_loop(self):
        """Main processing loop - monitors queue continuously"""
        print("🚀 Starting intelligent complaint processing loop...")
        print("📡 Monitoring queue for raw complaints...")
        
        consecutive_empty_checks = 0
        
        while self.is_running:
            try:
                # Get next raw complaint from queue
                queued_complaint = self.firebase_service.get_next_queued_complaint()
                
                if queued_complaint:
                    consecutive_empty_checks = 0
                    
                    # Process with full LLM intelligence
                    success = self.process_queued_complaint(queued_complaint)
                    
                    if success:
                        print(f"🎉 Complaint fully processed and queue cleaned!")
                    else:
                        print(f"⚠️ Processing completed with errors")
                        
                    print()  # Add spacing between complaints
                    
                else:
                    consecutive_empty_checks += 1
                    if consecutive_empty_checks % 20 == 1:  # Print every 20 empty checks
                        print("⏳ No raw complaints in queue, waiting for submissions...")
                    
                    time.sleep(3)  # Wait 3 seconds before next check
                    
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
        """Run processor in blocking mode"""
        self.is_running = True
        try:
            self.processing_loop()
        except KeyboardInterrupt:
            print("\n🛑 Processor stopped by user")
        finally:
            self.is_running = False

# =============== STANDALONE EXECUTION ===============
if __name__ == '__main__':
    print("🤖 CAMPUS GRIEVANCE PORTAL - INTELLIGENT LLM PROCESSOR")
    print("=" * 70)
    print("🧠 This service uses advanced LLM technology to:")
    print("   • Professionally rephrase raw complaints")
    print("   • Intelligently determine visibility levels")
    print("   • Accurately classify complaint categories")
    print("   • Route to appropriate authorities")
    print("🔄 Monitoring Firebase queue for raw submissions...")
    print("⏹️ Press Ctrl+C to stop")
    print("=" * 70)
    
    try:
        processor = IntelligentComplaintProcessor()
        processor.run_blocking()
    except KeyboardInterrupt:
        print("\n🛑 Intelligent Processor stopped by user")
    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        import traceback
        traceback.print_exc()
