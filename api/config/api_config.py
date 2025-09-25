import os
from dotenv import load_dotenv

load_dotenv()

class APIConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-key.json')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    
    # Complaint processing settings
    MAX_QUEUE_SIZE = 100
    PROCESSING_TIMEOUT = 300  # 5 minutes
