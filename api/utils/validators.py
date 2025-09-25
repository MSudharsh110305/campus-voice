from typing import Dict, Any
import re

def validate_complaint_submission(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complaint submission data"""
    errors = []
    
    # Required fields
    if not data.get('complaint_text'):
        errors.append('complaint_text is required')
    elif len(data['complaint_text'].strip()) < 10:
        errors.append('complaint_text must be at least 10 characters')
    elif len(data['complaint_text']) > 5000:
        errors.append('complaint_text cannot exceed 5000 characters')
    
    if not data.get('user_department'):
        errors.append('user_department is required')
    
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
        errors.append(f'Invalid user_department. Must be one of: {", ".join(valid_departments)}')
    
    # Email validation (if provided)
    if data.get('user_email'):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['user_email']):
            errors.append('Invalid email format')
    
    # Phone validation (if provided)
    if data.get('user_phone'):
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if not re.match(phone_pattern, data['user_phone'].replace(' ', '').replace('-', '')):
            errors.append('Invalid phone number format')
    
    # Visibility validation
    valid_visibilities = ['public', 'private', 'confidential']
    if data.get('visibility') and data['visibility'] not in valid_visibilities:
        errors.append(f'Invalid visibility. Must be one of: {", ".join(valid_visibilities)}')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_vote_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate voting data"""
    errors = []
    
    if not data.get('vote_type'):
        errors.append('vote_type is required')
    elif data['vote_type'] not in ['upvote', 'downvote']:
        errors.append('vote_type must be upvote or downvote')
    
    if not data.get('user_id'):
        errors.append('user_id is required')
    elif len(data['user_id'].strip()) < 3:
        errors.append('user_id must be at least 3 characters')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
