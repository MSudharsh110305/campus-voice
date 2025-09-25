import redis
import json
from typing import Dict, Any, Optional
from datetime import datetime
import os

class QueueManager:
    def __init__(self, redis_url: str = None):
        """Initialize Redis queue manager"""
        print("🔴 Initializing Real Redis Queue Manager...")
        
        if redis_url is None:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        
        try:
            self.redis_client = redis.from_url(redis_url)
            # Test connection
            self.redis_client.ping()
            print("✅ Redis connection established")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
            raise
        
        self.queue_key = 'complaint_processing_queue'
        self.processing_key = 'complaint_processing'
    
    def add_to_queue(self, complaint_id: str, complaint_data: Dict[str, Any]) -> int:
        """Add complaint to processing queue"""
        try:
            queue_item = {
                'complaint_id': complaint_id,
                'complaint_data': complaint_data,
                'queued_at': datetime.utcnow().isoformat()
            }
            
            # Add to queue (left push)
            queue_length = self.redis_client.lpush(self.queue_key, json.dumps(queue_item))
            
            print(f"✅ Redis: Added complaint {complaint_id} to queue (position: {queue_length})")
            return queue_length
            
        except Exception as e:
            print(f"❌ Redis queue error: {e}")
            raise
    
    def get_next_complaint(self) -> Optional[Dict[str, Any]]:
        """Get next complaint for processing (blocking)"""
        try:
            # Blocking right pop with 1 second timeout
            item = self.redis_client.brpop(self.queue_key, timeout=1)
            if item:
                complaint_data = json.loads(item[1])
                print(f"✅ Redis: Got complaint {complaint_data['complaint_id']} from queue")
                return complaint_data
            return None
            
        except Exception as e:
            print(f"❌ Redis dequeue error: {e}")
            return None
    
    def mark_processing(self, complaint_id: str):
        """Mark complaint as currently being processed"""
        try:
            self.redis_client.setex(
                f"{self.processing_key}:{complaint_id}",
                300,  # 5 minutes timeout
                datetime.utcnow().isoformat()
            )
            print(f"✅ Redis: Marked {complaint_id} as processing")
            
        except Exception as e:
            print(f"❌ Redis mark processing error: {e}")
    
    def mark_completed(self, complaint_id: str):
        """Mark complaint processing as completed"""
        try:
            self.redis_client.delete(f"{self.processing_key}:{complaint_id}")
            print(f"✅ Redis: Marked {complaint_id} as completed")
            
        except Exception as e:
            print(f"❌ Redis mark completed error: {e}")
    
    def get_queue_position(self, complaint_id: str) -> Dict[str, Any]:
        """Get complaint position in queue"""
        try:
            # Check if currently processing
            if self.redis_client.exists(f"{self.processing_key}:{complaint_id}"):
                return {
                    'queue_position': 0,
                    'status': 'processing'
                }
            
            # Check queue position
            queue_items = self.redis_client.lrange(self.queue_key, 0, -1)
            for i, item_json in enumerate(queue_items):
                item = json.loads(item_json)
                if item['complaint_id'] == complaint_id:
                    return {
                        'queue_position': i + 1,
                        'estimated_wait_minutes': (i + 1) * 2  # Estimate 2 min per complaint
                    }
            
            return {'queue_position': None}
            
        except Exception as e:
            print(f"❌ Redis position error: {e}")
            return {'queue_position': None}
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        try:
            queue_length = self.redis_client.llen(self.queue_key)
            processing_keys = self.redis_client.keys(f"{self.processing_key}:*")
            processing_count = len(processing_keys)
            
            return {
                'queued_complaints': queue_length,
                'processing_complaints': processing_count,
                'total_pending': queue_length + processing_count
            }
            
        except Exception as e:
            print(f"❌ Redis stats error: {e}")
            return {
                'queued_complaints': 0,
                'processing_complaints': 0,
                'total_pending': 0
            }
