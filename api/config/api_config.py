import os
from dotenv import load_dotenv

load_dotenv()

class APIConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'campus-grievance-portal-secret-key-2025')
    FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase-key.json')
    
    # Flask configuration
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
