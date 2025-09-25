from flask import jsonify
from datetime import datetime
from typing import Dict, Any, Optional

def success_response(data: Any, status_code: int = 200) -> tuple:
    """Format successful API response"""
    response = {
        'success': True,
        'data': data,
        'timestamp': datetime.utcnow().isoformat(),
        'status_code': status_code
    }
    return jsonify(response), status_code

def error_response(message: str, status_code: int = 400, details: Optional[Dict] = None) -> tuple:
    """Format error API response"""
    response = {
        'success': False,
        'error': {
            'message': message,
            'status_code': status_code
        },
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if details:
        response['error']['details'] = details
    
    return jsonify(response), status_code
