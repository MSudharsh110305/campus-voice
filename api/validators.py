"""
Request Validators - CampusVoice Complaint System
Version: 4.0.0 - Production Ready

Validates all API inputs with comprehensive checks:
- Complaint submissions
- Vote requests
- Status updates
- File uploads
- Pagination parameters
- Authority operations

Changes from v3.0:
- ✅ Changed user_id → roll_number
- ✅ Import departments/keywords from core.config
- ✅ Added vote validation
- ✅ Added status update validation
- ✅ Added file upload validation
- ✅ Added multiple images validation
- ✅ Added pagination validation
- ✅ Added roll number format validation
- ✅ Added input sanitization
- ✅ Added is_public field validation
"""

from typing import Dict, Any, Optional, List, Tuple
import base64
import re
import html
from werkzeug.datastructures import FileStorage

from core.config import get_config

# Get configuration
config = get_config()

# Import from config instead of hardcoding
VALID_DEPARTMENTS = config.departments
VALID_GENDERS = {'male', 'female', 'other'}
VALID_STATUSES = config.complaint_statuses  # ['raised', 'opened', 'reviewed', 'closed']
VALID_VOTE_TYPES = {'upvote', 'downvote', 'remove'}
VALID_CATEGORIES = config.categories  # ['academic', 'hostel', 'infrastructure']

# Authority roles
VALID_AUTHORITY_ROLES = list(config.authority_display_names.keys())

# Image settings from config
MAX_IMAGE_SIZE_MB = config.max_image_size_mb
MAX_IMAGES_PER_COMPLAINT = config.max_images_per_complaint
ALLOWED_IMAGE_FORMATS = config.allowed_image_formats


# =================== COMPLAINT SUBMISSION VALIDATION ===================

def validate_complaint_submission(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complaint submission with enhanced checks.
    
    Args:
        data: Request payload
    
    Returns:
        Dict with:
        - valid: bool
        - errors: List[str]
        - warnings: List[str]
        - sanitized_data: Dict (cleaned input)
    """
    errors = []
    warnings = []
    sanitized = {}
    
    # Check if payload is valid JSON
    if not isinstance(data, dict):
        return {
            'valid': False,
            'errors': ['Invalid payload: expected JSON object'],
            'warnings': [],
            'sanitized_data': {}
        }
    
    # =================== COMPLAINT TEXT ===================
    complaint_text = (data.get('complaint_text') or '').strip()
    
    if not complaint_text:
        errors.append('complaint_text is required')
    elif len(complaint_text) < config.min_complaint_length:
        errors.append(f'complaint_text must be at least {config.min_complaint_length} characters')
    elif len(complaint_text) > config.max_complaint_length:
        errors.append(f'complaint_text cannot exceed {config.max_complaint_length} characters')
    else:
        # Sanitize HTML/XSS
        sanitized['complaint_text'] = sanitize_text(complaint_text)
    
    # =================== ROLL NUMBER ===================
    roll_number = (data.get('roll_number') or '').strip()
    
    if not roll_number:
        errors.append('roll_number is required')
    else:
        roll_validation = validate_roll_number(roll_number)
        if not roll_validation['valid']:
            errors.extend(roll_validation['errors'])
        else:
            sanitized['roll_number'] = roll_number.upper()
    
    # =================== DEPARTMENT ===================
    department = (data.get('department') or '').strip()
    
    if not department:
        errors.append('department is required for proper routing')
    else:
        # Try to normalize department
        normalized_dept = config.normalize_department(department)
        if normalized_dept not in VALID_DEPARTMENTS:
            errors.append(
                f'Invalid department. Must be one of: {", ".join(VALID_DEPARTMENTS[:3])}... '
                f'(or use short forms like CSE, ECE, IT)'
            )
        else:
            sanitized['department'] = normalized_dept
    
    # =================== GENDER ===================
    gender = (data.get('gender') or '').strip().lower()
    
    if not gender:
        errors.append('gender is required')
    elif gender not in VALID_GENDERS:
        errors.append(f"gender must be one of: {', '.join(VALID_GENDERS)}")
    else:
        sanitized['gender'] = gender
    
    # =================== RESIDENCE ===================
    residence = (data.get('residence') or '').strip()
    
    if not residence:
        errors.append('residence is required (e.g., "Hostel A", "Day Scholar")')
    elif len(residence) > 256:
        errors.append('residence is too long (max 256 characters)')
    else:
        sanitized['residence'] = sanitize_text(residence)
    
    # =================== IS_PUBLIC (OPTIONAL) ===================
    is_public = data.get('is_public', False)
    
    if not isinstance(is_public, bool):
        # Try to convert string to bool
        if isinstance(is_public, str):
            is_public = is_public.lower() in ['true', '1', 'yes']
        else:
            is_public = bool(is_public)
    
    sanitized['is_public'] = is_public
    
    # =================== LEGACY FIELD WARNINGS ===================
    if 'user_id' in data:
        warnings.append('user_id is deprecated. Use roll_number instead.')
    
    if 'user_email' in data:
        warnings.append('user_email is deprecated and will be ignored')
    
    # =================== RETURN VALIDATION RESULT ===================
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'sanitized_data': sanitized
    }


# =================== ROLL NUMBER VALIDATION ===================

def validate_roll_number(roll_number: str) -> Dict[str, Any]:
    """
    Validate roll number format.
    
    Common patterns:
    - 21CS001, 22ECE045, 20IT123
    - CS21001, ECE22045
    
    Args:
        roll_number: Student roll number
    
    Returns:
        Dict with valid flag and errors
    """
    errors = []
    
    if not roll_number:
        return {'valid': False, 'errors': ['Roll number is required']}
    
    roll = roll_number.strip().upper()
    
    # Check length (typical range: 6-12 characters)
    if len(roll) < 5 or len(roll) > 15:
        errors.append('Roll number length must be between 5 and 15 characters')
    
    # Check if it contains alphanumeric characters
    if not re.match(r'^[A-Z0-9]+$', roll):
        errors.append('Roll number must contain only letters and numbers')
    
    # Optional: Check common patterns (customize for your college)
    # Pattern 1: 21CS001 (YY + DEPT + NUM)
    # Pattern 2: CS21001 (DEPT + YY + NUM)
    # Add your college-specific validation here if needed
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


# =================== VOTE VALIDATION ===================

def validate_vote_request(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate voting request.
    
    Args:
        data: {complaint_id, roll_number, vote_type}
    
    Returns:
        Dict with valid flag, errors, and sanitized data
    """
    errors = []
    sanitized = {}
    
    # ✅ Handle both URL param and body formats
    # Case 1: complaint_id in URL, roll_number + vote_type in body
    # Case 2: All three in body
    
    # Complaint ID (might come from URL path or body)
    complaint_id = (data.get('complaint_id') or '').strip()
    
    if not complaint_id:
        errors.append('complaint_id is required')
    else:
        id_validation = validate_complaint_id(complaint_id)
        if not id_validation['valid']:
            errors.extend(id_validation['errors'])
        else:
            sanitized['complaint_id'] = complaint_id
    
    # Roll number
    roll_number = (data.get('roll_number') or '').strip()
    
    if not roll_number:
        errors.append('roll_number is required')
    else:
        roll_validation = validate_roll_number(roll_number)
        if not roll_validation['valid']:
            errors.extend(roll_validation['errors'])
        else:
            sanitized['roll_number'] = roll_number.upper()
    
    # Vote type
    vote_type = (data.get('vote_type') or '').strip().lower()
    
    if not vote_type:
        errors.append('vote_type is required (upvote, downvote, or remove)')
    elif vote_type not in VALID_VOTE_TYPES:
        errors.append(f"vote_type must be one of: {', '.join(VALID_VOTE_TYPES)}")
    else:
        sanitized['vote_type'] = vote_type
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'sanitized_data': sanitized
    }


# =================== STATUS UPDATE VALIDATION ===================

def validate_status_update(data: Dict[str, Any], current_status: str) -> Dict[str, Any]:
    """
    Validate status update request from authority.
    
    Args:
        data: {complaint_id, new_status, updated_by, notes}
        current_status: Current complaint status
    
    Returns:
        Dict with valid flag, errors, and sanitized data
    """
    errors = []
    sanitized = {}
    
    # Complaint ID
    complaint_id = (data.get('complaint_id') or '').strip()
    
    if not complaint_id:
        errors.append('complaint_id is required')
    else:
        sanitized['complaint_id'] = complaint_id
    
    # New status
    new_status = (data.get('new_status') or '').strip().lower()
    
    if not new_status:
        errors.append('new_status is required')
    elif new_status not in VALID_STATUSES:
        errors.append(f"new_status must be one of: {', '.join(VALID_STATUSES)}")
    else:
        # Check if transition is valid (can only move forward)
        if not config.is_valid_status_transition(current_status, new_status):
            errors.append(
                f"Invalid status transition from '{current_status}' to '{new_status}'. "
                "Status can only move forward."
            )
        sanitized['new_status'] = new_status
    
    # Updated by (authority email/ID)
    updated_by = (data.get('updated_by') or '').strip()
    
    if not updated_by:
        errors.append('updated_by is required (authority identifier)')
    else:
        sanitized['updated_by'] = sanitize_text(updated_by)
    
    # Notes (optional)
    notes = (data.get('notes') or '').strip()
    
    if notes:
        if len(notes) > 1000:
            errors.append('notes cannot exceed 1000 characters')
        else:
            sanitized['notes'] = sanitize_text(notes)
    else:
        sanitized['notes'] = None
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'sanitized_data': sanitized
    }


# =================== FILE UPLOAD VALIDATION ===================

def validate_file_upload(file: FileStorage) -> Dict[str, Any]:
    """
    Validate file upload (Flask FileStorage object).
    
    Args:
        file: Werkzeug FileStorage object
    
    Returns:
        Dict with valid flag and errors
    """
    errors = []
    
    if not file:
        return {'valid': False, 'errors': ['No file provided']}
    
    # Check if file has a filename
    if not file.filename:
        errors.append('File has no filename')
        return {'valid': False, 'errors': errors}
    
    # Check file extension
    if not is_allowed_image_extension(file.filename):
        errors.append(
            f"Invalid file type. Allowed formats: {', '.join(ALLOWED_IMAGE_FORMATS)}"
        )
    
    # Check file size (read first chunk to estimate)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    
    if size > max_size_bytes:
        errors.append(
            f"File too large. Maximum size: {MAX_IMAGE_SIZE_MB}MB "
            f"(got {size / (1024*1024):.2f}MB)"
        )
    
    # Check MIME type
    if file.content_type and not file.content_type.startswith('image/'):
        errors.append(f"Invalid MIME type: {file.content_type}. Must be an image.")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_multiple_images(files: List[FileStorage]) -> Dict[str, Any]:
    """
    Validate multiple image uploads.
    
    Args:
        files: List of FileStorage objects
    
    Returns:
        Dict with valid flag, errors, and valid_files list
    """
    errors = []
    valid_files = []
    
    if not files:
        return {
            'valid': False,
            'errors': ['No files provided'],
            'valid_files': []
        }
    
    # Check count
    if len(files) > MAX_IMAGES_PER_COMPLAINT:
        errors.append(
            f"Too many files. Maximum {MAX_IMAGES_PER_COMPLAINT} images allowed "
            f"(got {len(files)})"
        )
        return {
            'valid': False,
            'errors': errors,
            'valid_files': []
        }
    
    # Validate each file
    for idx, file in enumerate(files):
        validation = validate_file_upload(file)
        if validation['valid']:
            valid_files.append(file)
        else:
            errors.append(f"File {idx + 1}: {'; '.join(validation['errors'])}")
    
    return {
        'valid': len(valid_files) > 0 and len(errors) == 0,
        'errors': errors,
        'valid_files': valid_files
    }


def validate_image_data(image_data: Optional[str]) -> Dict[str, Any]:
    """
    Validate base64-encoded image data.
    
    Args:
        image_data: Base64-encoded image string
    
    Returns:
        Dict with valid flag and errors list
    """
    errors = []
    
    if not image_data:
        return {'valid': True, 'errors': []}
    
    # Check if it's a string
    if not isinstance(image_data, str):
        errors.append('image_data must be a base64-encoded string')
        return {'valid': False, 'errors': errors}
    
    # Check for data URI scheme (optional)
    if image_data.startswith('data:image/'):
        # Extract base64 part
        match = re.match(r'data:image/[^;]+;base64,(.+)', image_data)
        if match:
            image_data = match.group(1)
        else:
            errors.append('Invalid data URI format')
            return {'valid': False, 'errors': errors}
    
    # Try to decode base64
    try:
        decoded = base64.b64decode(image_data, validate=True)
        
        # Check size
        max_size = MAX_IMAGE_SIZE_MB * 1024 * 1024
        if len(decoded) > max_size:
            errors.append(
                f'Image too large (max {MAX_IMAGE_SIZE_MB}MB, '
                f'got {len(decoded) / (1024*1024):.2f}MB)'
            )
        
        # Check if it looks like an image (magic bytes)
        if not _is_valid_image(decoded):
            errors.append(
                f'Invalid image format. Allowed: {", ".join(ALLOWED_IMAGE_FORMATS)}'
            )
    
    except Exception as e:
        errors.append(f'Invalid base64 encoding: {str(e)}')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def _is_valid_image(data: bytes) -> bool:
    """Check if bytes represent a valid image using magic bytes"""
    # JPEG magic bytes
    if data.startswith(b'\xff\xd8\xff'):
        return True
    
    # PNG magic bytes
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return True
    
    # WebP magic bytes
    if data.startswith(b'RIFF') and b'WEBP' in data[:16]:
        return True
    
    # GIF magic bytes (if allowed)
    if data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
        return True
    
    return False


def is_allowed_image_extension(filename: str) -> bool:
    """Check if image file extension is allowed"""
    if '.' not in filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_IMAGE_FORMATS


# =================== PAGINATION VALIDATION ===================

def validate_pagination_params(
    page: Any,
    limit: Any,
    max_limit: int = 100
) -> Dict[str, Any]:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (1-indexed)
        limit: Items per page
        max_limit: Maximum allowed limit
    
    Returns:
        Dict with valid flag, errors, and sanitized values
    """
    errors = []
    sanitized = {}
    
    # Validate page
    try:
        page_int = int(page) if page is not None else 1
        if page_int < 1:
            errors.append('page must be >= 1')
        else:
            sanitized['page'] = page_int
    except (ValueError, TypeError):
        errors.append('page must be a valid integer')
        sanitized['page'] = 1
    
    # Validate limit
    try:
        limit_int = int(limit) if limit is not None else 20
        if limit_int < 1:
            errors.append('limit must be >= 1')
        elif limit_int > max_limit:
            errors.append(f'limit cannot exceed {max_limit}')
            sanitized['limit'] = max_limit
        else:
            sanitized['limit'] = limit_int
    except (ValueError, TypeError):
        errors.append('limit must be a valid integer')
        sanitized['limit'] = 20
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'sanitized_data': sanitized
    }


# =================== COMPLAINT ID VALIDATION ===================

def validate_complaint_id(complaint_id: str) -> Dict[str, Any]:
    """
    Validate complaint ID format.
    
    Args:
        complaint_id: Complaint identifier
    
    Returns:
        Dict with valid flag and errors
    """
    errors = []
    
    if not complaint_id or not complaint_id.strip():
        return {'valid': False, 'errors': ['Complaint ID is required']}
    
    # Check length
    if len(complaint_id) < 10:
        errors.append('Invalid complaint ID format (too short)')
    
    # Check if it matches expected pattern (customize as needed)
    # Example: complaint_1234567890_abc123
    if not re.match(r'^[a-zA-Z0-9_-]+$', complaint_id):
        errors.append('Complaint ID contains invalid characters')
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


# =================== AUTHORITY VALIDATION ===================

def validate_authority_role(role: str) -> bool:
    """
    Check if authority role is valid.
    
    Args:
        role: Authority role (warden, hod, ao, principal, etc.)
    
    Returns:
        bool: True if valid
    """
    return role.lower() in VALID_AUTHORITY_ROLES


def validate_authority_filter(filters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate filter parameters for authority queries.
    
    Args:
        filters: Dict with status, priority, category, etc.
    
    Returns:
        Dict with valid flag, errors, and sanitized filters
    """
    errors = []
    sanitized = {}
    
    # Status filter
    if 'status' in filters and filters['status']:
        status = filters['status'].lower()
        if status not in VALID_STATUSES:
            errors.append(f"Invalid status filter: {status}")
        else:
            sanitized['status'] = status
    
    # Category filter
    if 'category' in filters and filters['category']:
        category = filters['category'].lower()
        if category not in VALID_CATEGORIES:
            errors.append(f"Invalid category filter: {category}")
        else:
            sanitized['category'] = category
    
    # Priority filter
    if 'priority' in filters and filters['priority']:
        priority = filters['priority'].capitalize()
        if priority not in ['Critical', 'High', 'Medium', 'Low']:
            errors.append(f"Invalid priority filter: {priority}")
        else:
            sanitized['priority'] = priority
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'sanitized_data': sanitized
    }


# =================== INPUT SANITIZATION ===================

def sanitize_text(text: str) -> str:
    """
    Sanitize text input to prevent XSS and injection attacks.
    
    Args:
        text: Raw text input
    
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Escape HTML entities
    sanitized = html.escape(text)
    
    # Remove null bytes
    sanitized = sanitized.replace('\x00', '')
    
    # Normalize whitespace (but preserve newlines)
    sanitized = re.sub(r'[ \t]+', ' ', sanitized)
    
    # Trim leading/trailing whitespace
    sanitized = sanitized.strip()
    
    return sanitized


# =================== UTILITY VALIDATORS ===================

def validate_department(department: str) -> bool:
    """Check if department is valid"""
    normalized = config.normalize_department(department)
    return normalized in VALID_DEPARTMENTS


def validate_gender(gender: str) -> bool:
    """Check if gender is valid"""
    return gender.strip().lower() in VALID_GENDERS


def validate_category(category: str) -> bool:
    """Check if category is valid"""
    return category.strip().lower() in VALID_CATEGORIES


def validate_email(email: str) -> bool:
    """Validate email format (for authority accounts)"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
