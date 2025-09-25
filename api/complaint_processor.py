import os
import sys
import time
import json

# Add project root to path FIRST
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add core directory to path  
sys.path.insert(0, os.path.join(project_root, 'core'))

# Import core modules DIRECTLY
from config import Config
from hybrid_classifier import CampusVoiceClassifier
from llm_engine import OllamaClient

# Import API modules
from api.firebase_service import FirebaseService
from api.queue_manager import QueueManager

class ComplaintProcessor:
    def __init__(self):
        print("🔧 Initializing Complaint Processor...")
        try:
            # Initialize services
            self.config = Config()
            self.firebase_service = FirebaseService()
            self.queue_manager = QueueManager()
            
            # Initialize AI components
            print("🤖 Loading AI models...")
            self.classifier = CampusVoiceClassifier(self.config)
            self.llm_client = OllamaClient(self.config)
            
            print("✅ Complaint Processor initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def process_complaint(self, complaint_data: dict) -> dict:
        """Process a single complaint through the LLM pipeline"""
        complaint_id = complaint_data['complaint_id']
        data = complaint_data['complaint_data']
        
        try:
            print(f"🔄 Processing complaint {complaint_id}...")
            
            # Mark as processing
            self.queue_manager.mark_processing(complaint_id)
            
            print(f"🧠 Running LLM classification for {complaint_id}...")
            
            # Run classification through your hybrid system
            result = self.classifier.classify(
                complaint=data['complaint_text'],
                user_department=data['user_department'],
                upvotes=0,
                image_data=data.get('image_data'),
                user_residence=data.get('user_residence')
            )
            
            print(f"✅ Classification complete: {result.category} -> {result.final_authority}")
            
            # Rephrase complaint using LLM
            print(f"✍️ Rephrasing complaint with LLM...")
            user_context = {
                'department': data['user_department'],
                'residence': data.get('user_residence'),
                'email': data.get('user_email')
            }
            
            rephrased = self.llm_client.rephrase_complaint(
                complaint=data['complaint_text'],
                user_context=user_context,
                image_data=data.get('image_data'),
                classification_hint=result.category
            )
            
            print(f"✅ Rephrasing complete")
            
            # Prepare processing result
            processing_result = {
                'category': result.category,
                'final_authority': result.final_authority,
                'routing_path': result.routing_path,
                'priority_level': result.priority_level,
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'rephrased_complaint': rephrased,
                'processing_time': result.processing_time,
                'model_used': result.model_used,
                'bypass_applied': result.bypass_applied,
                'used_image': result.used_image,
                'upvotes': result.upvotes
            }
            
            # Update Firebase with results
            print(f"🔥 Updating Firebase with results...")
            self.firebase_service.update_complaint_processing(complaint_id, processing_result)
            
            # Mark as completed
            self.queue_manager.mark_completed(complaint_id)
            
            print(f"🎉 Successfully processed complaint {complaint_id}")
            print(f"   Category: {result.category}")
            print(f"   Authority: {result.final_authority}")
            print(f"   Priority: {result.priority_level}")
            print(f"   Confidence: {result.confidence}")
            
            return processing_result
            
        except Exception as e:
            print(f"❌ Error processing complaint {complaint_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Mark as completed even on error
            self.queue_manager.mark_completed(complaint_id)
            
            # Update Firebase with error status
            error_result = {
                'category': 'infrastructure',  # fallback
                'final_authority': 'Administrative Officer (AO)',
                'routing_path': ['Error in processing - routed to AO'],
                'priority_level': 'Medium',
                'confidence': 'Low',
                'reasoning': f'Processing error: {str(e)}. Defaulted to infrastructure category.',
                'rephrased_complaint': data['complaint_text'],
                'processing_time': 0,
                'model_used': 'error_fallback',
                'bypass_applied': False,
                'used_image': False,
                'upvotes': 0
            }
            
            self.firebase_service.update_complaint_processing(complaint_id, error_result)
            return error_result
    
    def run_processor(self):
        """Main processing loop"""
        print("🚀 Starting complaint processor...")
        print("🔥 Connected to Firebase")
        print("🔴 Connected to Redis")
        print("🤖 AI models ready")
        print("⏳ Waiting for complaints to process...")
        
        processed_count = 0
        
        while True:
            try:
                # Get next complaint from queue (blocking call)
                complaint_data = self.queue_manager.get_next_complaint()
                
                if complaint_data:
                    processed_count += 1
                    print(f"\n🎯 Processing complaint #{processed_count}")
                    self.process_complaint(complaint_data)
                    print(f"✅ Total processed so far: {processed_count}\n")
                    
            except KeyboardInterrupt:
                print("🛑 Processor stopped by user")
                break
                
            except Exception as e:
                print(f"❌ Error in processor loop: {str(e)}")
                time.sleep(5)  # Wait before retrying

if __name__ == '__main__':
    try:
        processor = ComplaintProcessor()
        processor.run_processor()
    except KeyboardInterrupt:
        print("🛑 Processor stopped by user")
    except Exception as e:
        print(f"💥 Critical error: {e}")
        import traceback
        traceback.print_exc()
