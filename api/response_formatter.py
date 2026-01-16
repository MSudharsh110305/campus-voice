"""
Response Formatter - CampusVoice API
Version: 5.0.0 - Production Ready

Provides consistent JSON response formatting for all API endpoints.

Changes from v4.0:
- ✅ FIXED: Updated version to 5.0.0
- ✅ FIXED: All timestamps now timezone-aware (UTC)
- ✅ FIXED: Complete _build_metadata function
"""

from flask import jsonify, request
from datetime import datetime, timezone
from typing import Any, Optional, Dict, List
import uuid

# =================== RESPONSE FORMATTERS ===================

def success_response(
    data: Any,
    status_code: int = 200,
    message: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> tuple:
    """
    Format successful API response with consistent structure.
    
    Args:
        data: Response data (dict, list, or any JSON-serializable type)
        status_code: HTTP status code (default: 200)
        message: Optional success message
        metadata: Optional additional metadata
    
    Returns:
        Tuple of (jsonify response, status_code)
    """
    response = {
        'success': True,
        'data': data,
        'metadata': _build_metadata(status_code, metadata)
    }
    
    # Add optional message
    if message:
        response['message'] = message
    
    return jsonify(response), status_code


def error_response(
    message: str,
    status_code: int = 400,
    details: Optional[Dict] = None,
    error_code: Optional[str] = None
) -> tuple:
    """
    Format error API response with consistent structure.
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        details: Optional error details (validation errors, etc.)
        error_code: Optional error code for client-side handling
    
    Returns:
        Tuple of (jsonify response, status_code)
    """
    error_data = {
        'message': message,
        'status_code': status_code
    }
    
    # Add optional details (e.g., validation errors)
    if details:
        error_data['details'] = details
    
    # Add optional error code (e.g., 'INVALID_INPUT', 'NOT_FOUND')
    if error_code:
        error_data['code'] = error_code
    
    response = {
        'success': False,
        'error': error_data,
        'metadata': _build_metadata(status_code)
    }
    
    return jsonify(response), status_code


# =================== SPECIALIZED RESPONSE FORMATTERS ===================

def validation_error_response(
    errors: List[str],
    warnings: Optional[List[str]] = None
) -> tuple:
    """Format validation error response."""
    details = {'errors': errors}
    if warnings:
        details['warnings'] = warnings
    
    return error_response(
        message='Validation failed',
        status_code=400,
        details=details,
        error_code='VALIDATION_ERROR'
    )


def paginated_response(
    items: List[Any],
    page: int,
    limit: int,
    total: int,
    additional_data: Optional[Dict] = None
) -> tuple:
    """Format paginated response."""
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    
    data = {
        'items': items,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    # Add additional data (filters, sorting, etc.)
    if additional_data:
        data.update(additional_data)
    
    return success_response(data)


def created_response(
    resource_id: str,
    resource_type: str,
    data: Optional[Dict] = None,
    location: Optional[str] = None
) -> tuple:
    """Format resource creation response."""
    response_data = {
        'id': resource_id,
        'type': resource_type,
        'message': f'{resource_type.capitalize()} created successfully'
    }
    
    if data:
        response_data.update(data)
    
    if location:
        response_data['location'] = location
    
    return success_response(response_data, status_code=201)


def no_content_response() -> tuple:
    """Format no content response (204)."""
    return '', 204


# =================== HELPER FUNCTIONS ===================

def _build_metadata(status_code: int, extra_metadata: Optional[Dict] = None) -> Dict:
    """
    Build response metadata with timezone-aware timestamp.
    
    Args:
        status_code: HTTP status code
        extra_metadata: Optional additional metadata
    
    Returns:
        Metadata dictionary
    """
    metadata = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'api_version': '5.0.0',
        'status_code': status_code,
        'request_id': _get_request_id()
    }
    
    # Add path and method for debugging
    if request:
        metadata['path'] = request.path
        metadata['method'] = request.method
    
    # Add extra metadata if provided
    if extra_metadata:
        metadata.update(extra_metadata)
    
    return metadata


def _get_request_id() -> str:
    """
    Get or generate request ID for tracking.
    
    Returns:
        Request ID string
    """
    if request:
        # Check for existing request ID from headers
        request_id = request.headers.get('X-Request-ID')
        if request_id:
            return request_id
    
    # Generate new UUID
    return str(uuid.uuid4())


# =================== HTTP STATUS CODE HELPERS ===================

class HTTPStatus:
    """HTTP status code constants for easy reference."""
    
    # Success
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    
    # Client Errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    
    # Server Errors
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503


# =================== COMMON ERROR RESPONSES ===================

def not_found_response(resource_type: str = 'Resource') -> tuple:
    """Format 404 Not Found response."""
    return error_response(
        message=f'{resource_type} not found',
        status_code=HTTPStatus.NOT_FOUND,
        error_code='NOT_FOUND'
    )


def unauthorized_response(message: str = 'Authentication required') -> tuple:
    """Format 401 Unauthorized response."""
    return error_response(
        message=message,
        status_code=HTTPStatus.UNAUTHORIZED,
        error_code='UNAUTHORIZED'
    )


def forbidden_response(message: str = 'Access denied') -> tuple:
    """Format 403 Forbidden response."""
    return error_response(
        message=message,
        status_code=HTTPStatus.FORBIDDEN,
        error_code='FORBIDDEN'
    )


def conflict_response(message: str, details: Optional[Dict] = None) -> tuple:
    """Format 409 Conflict response."""
    return error_response(
        message=message,
        status_code=HTTPStatus.CONFLICT,
        details=details,
        error_code='CONFLICT'
    )


def internal_error_response(message: str = 'Internal server error') -> tuple:
    """Format 500 Internal Server Error response."""
    return error_response(
        message=message,
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        error_code='INTERNAL_ERROR'
    )


def rate_limit_response(retry_after: Optional[int] = None) -> tuple:
    """Format 429 Too Many Requests response."""
    details = {}
    if retry_after:
        details['retry_after'] = retry_after
    
    return error_response(
        message='Too many requests. Please try again later.',
        status_code=HTTPStatus.TOO_MANY_REQUESTS,
        details=details,
        error_code='RATE_LIMIT_EXCEEDED'
    )
