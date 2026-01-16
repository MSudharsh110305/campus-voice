"""
API Routes - CampusVoice Complaint System
Version: 5.0.0 - Production Ready

Complete REST API for complaint management:
- Student operations (submit, view, vote)
- Authority operations (view, update status, export)
- Public complaints (browse, vote)
- Image uploads (multipart/form-data)
- Statistics & analytics

Changes from v4.0:
- ✅ FIXED: Version updated to 5.0.0
- ✅ FIXED: All datetime.utcnow() replaced with datetime.now(timezone.utc)
- ✅ FIXED: Proper timezone import added
- ✅ FIXED: Consistent with all other v5.0 modules
- ✅ FIXED: Improved error handling and logging
"""

from flask import Blueprint, request, current_app, send_file
from datetime import datetime, timezone
from functools import wraps
import io

from api.models import ComplaintSubmission
from api.response_formatter import success_response, error_response
from api.validators import (
    validate_complaint_submission,
    validate_vote_request,
    validate_status_update,
    validate_pagination_params,
    validate_file_upload,
    validate_multiple_images
)

from core.config import get_config

config = get_config()
api_bp = Blueprint('api', '__name__')


# =================== ERROR HANDLING DECORATOR ===================

def handle_route_errors(func):
    """Decorator for consistent error handling across all routes."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return error_response(f"Invalid input: {str(e)}", 400)
        except KeyError as e:
            return error_response(f"Missing required field: {str(e)}", 400)
        except Exception as e:
            current_app.logger.error(f"Route error in {func.__name__}: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return error_response("Internal server error", 500)
    return wrapper


# =================== COMPLAINT SUBMISSION ===================

@api_bp.route('/complaints', methods=['POST'])
@handle_route_errors
def submit_complaint():
    """
    Submit a complaint (supports both JSON and multipart/form-data).
    
    JSON Format:
    {
        "roll_number": "21CS001",
        "department": "Computer Science & Engineering",
        "gender": "male",
        "residence": "Hostel A",
        "complaint_text": "WiFi not working in hostel...",
        "is_public": true,
        "image_data": "base64_encoded_image_string"  // OPTIONAL
    }
    
    Multipart Format:
    - roll_number, department, gender, residence, complaint_text, is_public (form fields)
    - images[] (files, up to 5)
    """
    # Handle JSON submission
    if request.is_json:
        data = request.get_json() or {}
        
        # Validate request data
        validation_result = validate_complaint_submission(data)
        if not validation_result['valid']:
            return error_response(
                "Validation failed",
                400,
                details={
                    'errors': validation_result['errors'],
                    'warnings': validation_result.get('warnings', [])
                }
            )
        
        # Create complaint submission
        submission = ComplaintSubmission(
            roll_number=validation_result['sanitized_data']['roll_number'],
            department=validation_result['sanitized_data']['department'],
            gender=validation_result['sanitized_data']['gender'],
            residence=validation_result['sanitized_data']['residence'],
            complaint_text=validation_result['sanitized_data']['complaint_text'],
            is_public=validation_result['sanitized_data'].get('is_public', False)
        )
        
        # Handle base64 image if provided
        image_files = None
        image_filenames = None
        if data.get('image_data'):
            # Convert base64 to bytes (handled by processor)
            image_files = [data['image_data']]
            image_filenames = ['uploaded_image.jpg']
    
    # Handle multipart/form-data submission
    else:
        # Extract form data
        form_data = {
            'roll_number': request.form.get('roll_number', ''),
            'department': request.form.get('department', ''),
            'gender': request.form.get('gender', ''),
            'residence': request.form.get('residence', ''),
            'complaint_text': request.form.get('complaint_text', ''),
            'is_public': request.form.get('is_public', 'false').lower() == 'true'
        }
        
        # Validate form data
        validation_result = validate_complaint_submission(form_data)
        if not validation_result['valid']:
            return error_response(
                "Validation failed",
                400,
                details={
                    'errors': validation_result['errors'],
                    'warnings': validation_result.get('warnings', [])
                }
            )
        
        # Create complaint submission
        submission = ComplaintSubmission(
            roll_number=validation_result['sanitized_data']['roll_number'],
            department=validation_result['sanitized_data']['department'],
            gender=validation_result['sanitized_data']['gender'],
            residence=validation_result['sanitized_data']['residence'],
            complaint_text=validation_result['sanitized_data']['complaint_text'],
            is_public=form_data['is_public']
        )
        
        # Handle file uploads
        image_files = None
        image_filenames = None
        if 'images' in request.files:
            files = request.files.getlist('images')
            
            # Validate images
            img_validation = validate_multiple_images(files)
            if not img_validation['valid']:
                return error_response(
                    "Image validation failed",
                    400,
                    details={'errors': img_validation['errors']}
                )
            
            image_files = img_validation['valid_files']
            image_filenames = [f.filename for f in image_files]
    
    # Process complaint
    processor = current_app.complaint_processor
    success, message, complaint = processor.process_complaint(
        submission,
        image_files,
        image_filenames
    )
    
    if not success:
        return error_response(message, 500)
    
    # Build response
    response_data = {
        'complaint_id': complaint.complaint_id,
        'status': complaint.status,
        'category': complaint.category,
        'assigned_authority': complaint.assigned_authority,
        'priority_level': complaint.priority_level,
        'priority_score': complaint.priority_score,
        'is_public': complaint.is_public,
        'requires_image': complaint.requires_image,
        'image_requirement_reason': complaint.image_requirement_reason,
        'is_mandatory_image': complaint.is_mandatory_image,
        'images_uploaded': len(complaint.image_urls),
        'processing_time': complaint.processing_time,
        'message': 'Complaint submitted and processed successfully',
        'next_steps': [
            f"Track your complaint at: /api/v1/complaints/{complaint.complaint_id}",
            f"View your complaints at: /api/v1/complaints/student/{submission.roll_number}",
        ]
    }
    
    # Add warnings if any
    if validation_result.get('warnings'):
        response_data['warnings'] = validation_result['warnings']
    
    return success_response(response_data, 201)


# =================== IMAGE REQUIREMENT CHECK ===================

@api_bp.route('/complaints/check-image-requirement', methods=['POST'])
@handle_route_errors
def check_image_requirement():
    """
    Check if complaint needs an image using smart LLM detection.
    POST: {"complaint_text": "Water tap is leaking"}
    Returns: {"needs_image": true, "reason": "...", "is_mandatory": true}
    """
    data = request.get_json() or {}
    complaint_text = data.get('complaint_text', '').strip()
    
    if not complaint_text:
        return error_response("complaint_text is required", 400)
    
    if len(complaint_text) < config.min_complaint_length:
        return error_response(
            f"complaint_text too short (minimum {config.min_complaint_length} characters)",
            400
        )
    
    # Use smart image detection from LLM engine
    llm_engine = current_app.llm_engine
    needs_image, reason, is_mandatory = llm_engine.check_if_image_needed(complaint_text)
    
    return success_response({
        'needs_image': needs_image,
        'reason': reason,
        'is_mandatory': is_mandatory,
        'complaint_preview': complaint_text[:100] + ('...' if len(complaint_text) > 100 else ''),
        'recommendation': (
            'Image is required for processing' if is_mandatory
            else 'Upload image for faster resolution' if needs_image
            else 'Image not required'
        )
    })


# =================== COMPLAINT RETRIEVAL ===================

@api_bp.route('/complaints/<complaint_id>', methods=['GET'])
@handle_route_errors
def get_complaint(complaint_id):
    """Get single complaint by ID."""
    firebase_service = current_app.firebase_service
    complaint = firebase_service.get_complaint(complaint_id)
    
    if not complaint:
        return error_response("Complaint not found", 404)
    
    # Determine which view to return based on requester
    # For now, return student view (in production, check authentication)
    from api.models import complaint_to_student_view
    view = complaint_to_student_view(complaint)
    
    return success_response(view.to_dict())


@api_bp.route('/complaints/student/<roll_number>', methods=['GET'])
@handle_route_errors
def get_student_complaints(roll_number):
    """
    Get complaints submitted by a student.
    Query params:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - status: Filter by status (raised/opened/reviewed/closed)
    - category: Filter by category (academic/hostel/infrastructure)
    """
    # Validate pagination
    page = request.args.get('page', 1)
    limit = request.args.get('limit', 20)
    
    pagination = validate_pagination_params(page, limit)
    if not pagination['valid']:
        return error_response(
            "Invalid pagination parameters",
            400,
            details={'errors': pagination['errors']}
        )
    
    # Build filters
    filters = {}
    if request.args.get('status'):
        filters['status'] = request.args.get('status')
    if request.args.get('category'):
        filters['category'] = request.args.get('category')
    
    # Get complaints
    firebase_service = current_app.firebase_service
    complaints, total = firebase_service.get_student_complaints(
        roll_number,
        filters,
        pagination['sanitized_data']['page'],
        pagination['sanitized_data']['limit']
    )
    
    return success_response({
        'complaints': [c.to_dict() for c in complaints],
        'pagination': {
            'page': pagination['sanitized_data']['page'],
            'limit': pagination['sanitized_data']['limit'],
            'total': total,
            'total_pages': (total + pagination['sanitized_data']['limit'] - 1) // pagination['sanitized_data']['limit']
        },
        'filters': filters
    })


@api_bp.route('/complaints/authority/<authority_name>', methods=['GET'])
@handle_route_errors
def get_authority_complaints(authority_name):
    """
    Get complaints assigned to an authority.
    Query params:
    - page, limit, status, priority, category (same as student view)
    
    TODO: Add authentication to verify authority identity
    """
    # Validate pagination
    page = request.args.get('page', 1)
    limit = request.args.get('limit', 20)
    
    pagination = validate_pagination_params(page, limit)
    if not pagination['valid']:
        return error_response(
            "Invalid pagination parameters",
            400,
            details={'errors': pagination['errors']}
        )
    
    # Build filters
    filters = {}
    for param in ['status', 'priority', 'category']:
        if request.args.get(param):
            filters[param] = request.args.get(param)
    
    # Get complaints
    firebase_service = current_app.firebase_service
    complaints, total = firebase_service.get_complaints_by_authority(
        authority_name,
        filters,
        pagination['sanitized_data']['page'],
        pagination['sanitized_data']['limit']
    )
    
    return success_response({
        'authority': authority_name,
        'complaints': [c.to_dict() for c in complaints],
        'pagination': {
            'page': pagination['sanitized_data']['page'],
            'limit': pagination['sanitized_data']['limit'],
            'total': total,
            'total_pages': (total + pagination['sanitized_data']['limit'] - 1) // pagination['sanitized_data']['limit']
        },
        'filters': filters
    })


@api_bp.route('/complaints/public', methods=['GET'])
@handle_route_errors
def get_public_complaints():
    """
    Get public complaints for browsing and voting.
    Query params:
    - page, limit, category, priority
    - sort_by: created_at, net_votes, priority_score (default: created_at)
    - sort_order: asc, desc (default: desc)
    """
    # Validate pagination
    page = request.args.get('page', 1)
    limit = request.args.get('limit', 20)
    
    pagination = validate_pagination_params(page, limit)
    if not pagination['valid']:
        return error_response(
            "Invalid pagination parameters",
            400,
            details={'errors': pagination['errors']}
        )
    
    # Build filters
    filters = {}
    for param in ['category', 'priority']:
        if request.args.get(param):
            filters[param] = request.args.get(param)
    
    # Sorting
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by not in ['created_at', 'net_votes', 'priority_score']:
        sort_by = 'created_at'
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Get complaints
    firebase_service = current_app.firebase_service
    complaints, total = firebase_service.get_public_complaints(
        filters,
        pagination['sanitized_data']['page'],
        pagination['sanitized_data']['limit'],
        sort_by,
        sort_order
    )
    
    return success_response({
        'complaints': [c.to_dict() for c in complaints],
        'pagination': {
            'page': pagination['sanitized_data']['page'],
            'limit': pagination['sanitized_data']['limit'],
            'total': total,
            'total_pages': (total + pagination['sanitized_data']['limit'] - 1) // pagination['sanitized_data']['limit']
        },
        'filters': filters,
        'sorting': {
            'sort_by': sort_by,
            'sort_order': sort_order
        }
    })


# =================== STATUS UPDATES ===================

@api_bp.route('/complaints/<complaint_id>/status', methods=['PUT'])
@handle_route_errors
def update_complaint_status(complaint_id):
    """
    Update complaint status (authority only).
    PUT: {
        "new_status": "opened",
        "updated_by": "hod.cse@college.edu",
        "notes": "Looking into this issue"
    }
    
    TODO: Add authentication to verify authority identity
    """
    data = request.get_json() or {}
    
    # Get current complaint
    firebase_service = current_app.firebase_service
    complaint = firebase_service.get_complaint(complaint_id)
    
    if not complaint:
        return error_response("Complaint not found", 404)
    
    # Validate status update
    validation = validate_status_update(data, complaint.status)
    if not validation['valid']:
        return error_response(
            "Validation failed",
            400,
            details={'errors': validation['errors']}
        )
    
    # Update status
    success = firebase_service.update_status(
        complaint_id,
        validation['sanitized_data']['new_status'],
        validation['sanitized_data']['updated_by'],
        validation['sanitized_data'].get('notes')
    )
    
    if not success:
        return error_response("Failed to update status", 500)
    
    return success_response({
        'complaint_id': complaint_id,
        'old_status': complaint.status,
        'new_status': validation['sanitized_data']['new_status'],
        'updated_by': validation['sanitized_data']['updated_by'],
        'message': 'Status updated successfully'
    })


# =================== VOTING SYSTEM ===================

@api_bp.route('/complaints/<complaint_id>/vote', methods=['POST'])
@handle_route_errors
def vote_on_complaint(complaint_id):
    """
    Vote on a public complaint.
    POST: {
        "roll_number": "21CS001",
        "vote_type": "upvote"  // or "downvote" or "remove"
    }
    """
    data = request.get_json() or {}
    data['complaint_id'] = complaint_id
    
    # Debug logging
    print(f"\n🗳️  Vote request received:")
    print(f"   Complaint ID: {complaint_id}")
    print(f"   Request Data: {data}")
    print(f"   Content-Type: {request.content_type}")
    
    # Validate vote request
    validation = validate_vote_request(data)
    if not validation['valid']:
        print(f"❌ Validation failed: {validation['errors']}")
        return error_response(
            "Validation failed",
            400,
            details={'errors': validation['errors']}
        )
    
    print(f"✅ Validation passed: {validation['sanitized_data']}")
    
    # Record vote
    firebase_service = current_app.firebase_service
    result = firebase_service.vote_on_complaint(
        validation['sanitized_data']['complaint_id'],
        validation['sanitized_data']['roll_number'],
        validation['sanitized_data']['vote_type']
    )
    
    print(f"📊 Firebase result: {result}")
    
    if result['success']:
        print(f"✅ Vote successful!")
        return success_response({
            'message': result['message'],
            'complaint_id': complaint_id,
            'vote_type': validation['sanitized_data']['vote_type']
        })
    else:
        print(f"❌ Voting failed: {result['message']}")
        return error_response(result['message'], 400)


@api_bp.route('/complaints/<complaint_id>/vote', methods=['DELETE'])
@handle_route_errors
def remove_vote(complaint_id):
    """
    Remove vote from a complaint.
    Query param: roll_number
    """
    roll_number = request.args.get('roll_number')
    if not roll_number:
        return error_response("roll_number query parameter is required", 400)
    
    firebase_service = current_app.firebase_service
    result = firebase_service.vote_on_complaint(
        complaint_id,
        roll_number,
        'remove'
    )
    
    if result['success']:
        return success_response({
            'message': 'Vote removed successfully',
            'complaint_id': complaint_id
        })
    else:
        return error_response(result['message'], 400)


# =================== IMAGE UPLOADS ===================

@api_bp.route('/complaints/<complaint_id>/images', methods=['POST'])
@handle_route_errors
def upload_complaint_images(complaint_id):
    """
    Upload images to an existing complaint.
    Multipart form-data with 'images[]' field (up to 5 files)
    """
    # Check if complaint exists
    firebase_service = current_app.firebase_service
    complaint = firebase_service.get_complaint(complaint_id)
    
    if not complaint:
        return error_response("Complaint not found", 404)
    
    # Check if files provided
    if 'images' not in request.files:
        return error_response("No images provided", 400)
    
    files = request.files.getlist('images')
    
    # Validate images
    validation = validate_multiple_images(files)
    if not validation['valid']:
        return error_response(
            "Image validation failed",
            400,
            details={'errors': validation['errors']}
        )
    
    # Upload images
    image_urls = firebase_service.upload_multiple_images(
        complaint_id,
        validation['valid_files'],
        [f.filename for f in validation['valid_files']]
    )
    
    if not image_urls:
        return error_response("Failed to upload images", 500)
    
    return success_response({
        'complaint_id': complaint_id,
        'images_uploaded': len(image_urls),
        'image_urls': image_urls,
        'message': 'Images uploaded successfully'
    })


# =================== EXPORT FUNCTIONALITY ===================

@api_bp.route('/complaints/authority/<authority_name>/export', methods=['GET'])
@handle_route_errors
def export_complaints_csv(authority_name):
    """
    Export complaints as CSV (authority only).
    Query params: status, priority, category (filters)
    
    TODO: Add authentication to verify authority identity
    """
    # Build filters
    filters = {}
    for param in ['status', 'priority', 'category']:
        if request.args.get(param):
            filters[param] = request.args.get(param)
    
    # Get CSV
    firebase_service = current_app.firebase_service
    csv_data = firebase_service.export_complaints_csv(authority_name, filters)
    
    if not csv_data:
        return error_response("Failed to generate CSV", 500)
    
    # Create file response
    output = io.BytesIO()
    output.write(csv_data.encode('utf-8'))
    output.seek(0)
    
    # ✅ FIXED: Use timezone-aware datetime
    filename = f"complaints_{authority_name.replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


# =================== STATISTICS & ANALYTICS ===================

@api_bp.route('/statistics/system', methods=['GET'])
@handle_route_errors
def get_system_statistics():
    """Get comprehensive system statistics."""
    firebase_service = current_app.firebase_service
    stats = firebase_service.get_system_statistics()
    
    return success_response(stats.to_dict())


@api_bp.route('/statistics/monthly/<year_month>', methods=['GET'])
@handle_route_errors
def get_monthly_statistics(year_month):
    """
    Get monthly statistics.
    Example: /api/v1/statistics/monthly/2025-12
    """
    # Validate format (YYYY-MM)
    import re
    if not re.match(r'^\d{4}-\d{2}$', year_month):
        return error_response("Invalid format. Use YYYY-MM (e.g., 2025-12)", 400)
    
    firebase_service = current_app.firebase_service
    stats = firebase_service.get_monthly_statistics(year_month)
    
    return success_response(stats.to_dict())


@api_bp.route('/statistics/authority/<authority_name>', methods=['GET'])
@handle_route_errors
def get_authority_statistics(authority_name):
    """Get statistics for a specific authority."""
    firebase_service = current_app.firebase_service
    stats = firebase_service.get_authority_statistics(authority_name)
    
    return success_response(stats.to_dict())


# =================== SYSTEM INFORMATION ===================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Fast health check."""
    try:
        # Check services
        processor_status = "running" if hasattr(current_app, 'complaint_processor') else "not_initialized"
        llm_status = "configured" if hasattr(current_app, 'llm_engine') else "not_configured"
        firebase_status = "connected" if hasattr(current_app, 'firebase_service') else "not_connected"
        
        return success_response({
            'api_status': 'healthy',
            'firebase_status': firebase_status,
            'complaint_processor_status': processor_status,
            'llm_engine_status': llm_status,
            'llm_model': config.groq_model,
            'version': '5.0.0',  # ✅ FIXED: Updated version
            'features': [
                'Concurrent processing',
                'Smart image detection',
                'Groq LLM processing',
                'Authority routing',
                'Priority scoring',
                'Visibility filtering',
                'Pseudo-anonymity',
                'Abusive language detection'  # ✅ ADDED: v5.0 feature
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()  # ✅ FIXED: timezone-aware
        })
    
    except Exception as e:
        return error_response(f"Health check failed: {str(e)}", 500)


@api_bp.route('/config/departments', methods=['GET'])
def get_departments():
    """Get list of available departments."""
    return success_response({
        'departments': config.departments,
        'total_count': len(config.departments),
        'note': 'Select your department for accurate complaint routing'
    })


@api_bp.route('/config/categories', methods=['GET'])
def get_categories():
    """Get list of complaint categories."""
    return success_response({
        'categories': config.categories,
        'total_count': len(config.categories)
    })


@api_bp.route('/config/statuses', methods=['GET'])
def get_statuses():
    """Get list of complaint statuses."""
    return success_response({
        'statuses': config.complaint_statuses,
        'total_count': len(config.complaint_statuses),
        'note': 'Status transitions: raised → opened → reviewed → closed'
    })


@api_bp.route('/config/authorities', methods=['GET'])
def get_authorities():
    """Get list of authority roles."""
    return success_response({
        'authorities': list(config.authority_display_names.values()),
        'authority_types': list(config.authority_display_names.keys()),
        'total_count': len(config.authority_display_names)
    })


# =================== LLM CAPABILITIES INFO ===================

@api_bp.route('/llm/capabilities', methods=['GET'])
def get_llm_capabilities():
    """Get information about LLM processing capabilities."""
    return success_response({
        'llm_model': {
            'provider': 'Groq',
            'model': config.groq_model,
            'speed': 'Ultra-fast (< 2 seconds per complaint)',
            'quality': 'High accuracy with context awareness'
        },
        'processing_features': {
            'professional_rephrasing': {
                'description': 'Converts casual complaints into formal language',
                'benefit': 'Appropriate tone for official submission'
            },
            'smart_image_detection': {
                'description': 'Automatically detects if image is required or recommended',
                'levels': ['Not needed', 'Recommended', 'Mandatory'],
                'benefit': 'Faster resolution with visual evidence when needed'
            },
            'visibility_determination': {
                'description': 'Determines public/private/confidential status',
                'levels': ['public', 'private', 'confidential'],
                'benefit': 'Appropriate privacy protection'
            },
            'smart_categorization': {
                'description': 'Classifies complaints accurately',
                'categories': config.categories,
                'benefit': 'Proper routing and handling'
            },
            'authority_routing': {
                'description': 'Routes to appropriate authority with conflict detection',
                'features': ['Department-specific routing', 'Bypass for conflicts', 'Escalation support'],
                'benefit': 'Faster resolution by reaching right person'
            },
            'priority_scoring': {
                'description': 'Calculates priority level',
                'levels': ['Critical', 'High', 'Medium', 'Low'],
                'factors': ['Keywords', 'Image requirement', 'Voting support'],
                'benefit': 'Critical issues get immediate attention'
            },
            'abusive_language_detection': {  # ✅ ADDED: v5.0 feature
                'description': 'Detects and handles inappropriate language',
                'actions': ['Flag user', 'Clean text', 'Track violations'],
                'benefit': 'Maintains professional environment'
            }
        },
        'privacy_protection': {
            'pseudo_anonymity': 'SHA-256 hashed roll numbers',
            'sensitive_detection': 'Automatic confidential content identification',
            'visibility_filtering': 'Authorities see only relevant complaints',
            'secure_handling': 'Appropriate visibility levels for sensitive issues'
        }
    })


# =================== ERROR HANDLERS ===================

@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return error_response("Endpoint not found", 404)


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return error_response("Method not allowed", 405)


@api_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    current_app.logger.error(f"Internal error: {error}")
    return error_response("Internal server error", 500)
