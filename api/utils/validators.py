from typing import Dict, Any
import re

def validate_anonymous_complaint_submission(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pseudo-anonymous complaint submission"""
    errors = []
    
    # Required fields
    if not data.get('complaint_text'):
        errors.append('complaint_text is required')
    elif len(data['complaint_text'].strip()) < 15:
        errors.append('complaint_text must be at least 15 characters for meaningful processing')
    elif len(data['complaint_text']) > 2000:
        errors.append('complaint_text cannot exceed 2000 characters')
    
    if not data.get('user_department'):
        errors.append('user_department is required for proper routing')
    
    # Valid departments
    valid_departments = [
        'Electronics & Communication Engineering',
        'Computer Science & Engineering',
        'Robotics and Automation',
        'Mechanical Engineering',
        'Electrical & Electronics Engineering',
        'Electronics & Instrumentation Engineering',
        'Biomedical Engineering',
        'Aeronautical Engineering',
        'Civil Engineering',
        'Information Technology',
        'Management Studies',
        'Artificial Intelligence and Data Science'
    ]
    
    if data.get('user_department') and data['user_department'] not in valid_departments:
        errors.append(f'Invalid user_department. Must be one of the listed engineering departments.')
    
    # Email validation (if provided - optional for anonymity)
    if data.get('user_email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['user_email']):
            errors.append('Invalid email format')
    
    # Image data validation (if provided)
    if data.get('image_data'):
        if len(data['image_data']) > 5 * 1024 * 1024:  # 5MB limit
            errors.append('Image data too large (max 5MB)')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
