from typing import Dict, Any

VALID_DEPARTMENTS = [
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

VALID_GENDERS = {'male', 'female', 'other'}

def validate_anonymous_complaint_submission(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate pseudo-anonymous text-only complaint submission (with user_id/gender/residence)."""
    errors = []

    # Required payload presence
    if not isinstance(data, dict):
        return {'valid': False, 'errors': ['Invalid payload: expected JSON object']}

    # complaint_text
    complaint_text = (data.get('complaint_text') or '').strip()
    if not complaint_text:
        errors.append('complaint_text is required')
    elif len(complaint_text) < 15:
        errors.append('complaint_text must be at least 15 characters for meaningful processing')
    elif len(complaint_text) > 2000:
        errors.append('complaint_text cannot exceed 2000 characters')

    # user_id (mandatory)
    user_id = (data.get('user_id') or '').strip()
    if not user_id:
        errors.append('user_id is required')
    elif len(user_id) > 128:
        errors.append('user_id is too long (max 128 characters)')

    # gender (mandatory, enumerated)
    gender = (data.get('gender') or '').strip().lower()
    if not gender:
        errors.append('gender is required')
    elif gender not in VALID_GENDERS:
        errors.append("gender must be one of: male, female, other")

    # user_department (mandatory, must be in list)
    user_department = (data.get('user_department') or '').strip()
    if not user_department:
        errors.append('user_department is required for proper routing')
    elif user_department not in VALID_DEPARTMENTS:
        errors.append('Invalid user_department. Must be one of the listed engineering departments.')

    # user_residence (mandatory)
    user_residence = (data.get('user_residence') or '').strip()
    if not user_residence:
        errors.append('user_residence is required')

    # Explicitly forbid legacy fields for clarity (optional but recommended)
    if 'user_email' in data and data.get('user_email'):
        errors.append('user_email is not supported; use user_id for pseudo-anonymity')
    if 'image_data' in data and data.get('image_data'):
        errors.append('image_data is not supported; only text complaints are accepted')

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
