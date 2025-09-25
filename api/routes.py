from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import base64
import io
from PIL import Image

from api.models import ComplaintSubmission
from api.utils.response_formatter import success_response, error_response
from api.utils.validators import validate_complaint_submission, validate_vote_data

api_bp = Blueprint('api', __name__)

# =================== COMPLAINT SUBMISSION ===================

@api_bp.route('/complaints', methods=['POST'])
def submit_complaint():
    """
    Submit a new complaint for LLM processing
    
    Expected JSON:
    {
        "complaint_text": "The hostel wifi is very slow...",
        "user_department": "Computer Science & Engineering",
        "user_residence": "Hostel A", // optional
        "user_email": "student@college.edu", // optional
        "user_phone": "+919876543210", // optional
        "image_data": "base64_encoded_image", // optional
        "visibility": "public" // public, private, confidential
    }
    """
    try:
        data = request.get_json()
        
        # Validate input data
        validation_result = validate_complaint_submission(data)
        if not validation_result['valid']:
            return error_response(validation_result['errors'], 400)
        
        # Handle image validation if present
        if data.get('image_data'):
            try:
                # Decode and validate image
                img_binary = base64.b64decode(data['image_data'])
                Image.open(io.BytesIO(img_binary))
            except Exception as e:
                return error_response(f"Invalid image data: {str(e)}", 400)
        
        # Create complaint submission model
        submission = ComplaintSubmission(
            complaint_text=data['complaint_text'],
            user_department=data['user_department'],
            user_residence=data.get('user_residence'),
            user_email=data.get('user_email'),
            user_phone=data.get('user_phone'),
            image_data=data.get('image_data'),
            visibility=data.get('visibility', 'public')
        )
        
        # Submit to Firebase queue
        firebase_service = current_app.firebase_service
        complaint_id, queue_position = firebase_service.submit_complaint(submission)
        
        # Calculate estimated processing time (2 minutes per complaint in queue)
        estimated_minutes = queue_position * 2
        
        return success_response({
            'complaint_id': complaint_id,
            'status': 'queued_for_processing',
            'queue_position': queue_position,
            'estimated_processing_time_minutes': estimated_minutes,
            'message': 'Complaint submitted successfully and queued for LLM processing',
            'next_steps': [
                'Your complaint is being processed by our AI system',
                'Classification and routing will be completed automatically',
                'You will receive an appropriate authority assignment',
                'Check status using the complaint_id'
            ]
        }, 201)
        
    except Exception as e:
        return error_response(f"Submission failed: {str(e)}", 500)

# =================== COMPLAINT STATUS & RETRIEVAL ===================

@api_bp.route('/complaints/<complaint_id>/status', methods=['GET'])
def get_complaint_status(complaint_id):
    """Get detailed complaint status and processing results"""
    try:
        firebase_service = current_app.firebase_service
        complaint_data = firebase_service.get_complaint_status(complaint_id)
        
        if not complaint_data:
            return error_response("Complaint not found", 404)
        
        # Add helpful status information
        location = complaint_data.get('location', 'unknown')
        
        if location == 'queue':
            status_info = {
                'processing_stage': 'In Queue',
                'description': 'Waiting for LLM processing',
                'current_status': complaint_data.get('status', 'pending')
            }
        elif 'processed_complaints' in location:
            status_info = {
                'processing_stage': 'Completed',
                'description': 'Successfully processed and categorized',
                'current_status': 'processed',
                'category': complaint_data.get('classification'),
                'authority': complaint_data.get('final_authority')
            }
        elif location == 'public':
            status_info = {
                'processing_stage': 'Public',
                'description': 'Available for community voting',
                'current_status': 'public',
                'upvotes': complaint_data.get('upvotes', 0),
                'downvotes': complaint_data.get('downvotes', 0)
            }
        elif location == 'private':
            status_info = {
                'processing_stage': 'Private',
                'description': 'Stored as private/confidential',
                'current_status': 'private'
            }
        else:
            status_info = {
                'processing_stage': 'Unknown',
                'description': 'Status could not be determined',
                'current_status': 'unknown'
            }
        
        # Combine complaint data with status info
        response_data = {
            **complaint_data,
            'status_info': status_info
        }
        
        return success_response(response_data)
        
    except Exception as e:
        return error_response(f"Status retrieval failed: {str(e)}", 500)

@api_bp.route('/complaints/public', methods=['GET'])
def get_public_complaints():
    """Get public complaints available for voting"""
    try:
        category = request.args.get('category')  # infrastructure, academic, hostel
        limit = min(int(request.args.get('limit', 50)), 100)
        
        firebase_service = current_app.firebase_service
        complaints = firebase_service.get_public_complaints(category, limit)
        
        return success_response({
            'complaints': complaints,
            'total_returned': len(complaints),
            'category_filter': category,
            'limit_applied': limit,
            'available_categories': ['infrastructure', 'academic', 'hostel']
        })
        
    except Exception as e:
        return error_response(f"Public complaints retrieval failed: {str(e)}", 500)

@api_bp.route('/complaints/categories/<category>', methods=['GET'])
def get_complaints_by_category(category):
    """Get complaints filtered by LLM classification"""
    try:
        if category not in ['infrastructure', 'academic', 'hostel']:
            return error_response(
                "Invalid category. Must be one of: infrastructure, academic, hostel", 
                400
            )
        
        department = request.args.get('department')  # For academic complaints
        limit = min(int(request.args.get('limit', 50)), 100)
        
        firebase_service = current_app.firebase_service
        complaints = firebase_service.get_complaints_by_category(category, department)
        
        # Limit results
        limited_complaints = complaints[:limit] if len(complaints) > limit else complaints
        
        return success_response({
            'category': category,
            'department_filter': department,
            'complaints': limited_complaints,
            'total_found': len(complaints),
            'total_returned': len(limited_complaints)
        })
        
    except Exception as e:
        return error_response(f"Category retrieval failed: {str(e)}", 500)

# =================== VOTING SYSTEM ===================

@api_bp.route('/complaints/<complaint_id>/vote', methods=['POST'])
def vote_on_complaint(complaint_id):
    """
    Vote on a public complaint
    
    Expected JSON:
    {
        "user_id": "student123",
        "vote_type": "upvote" // upvote or downvote
    }
    """
    try:
        data = request.get_json()
        
        # Validate vote data
        validation_result = validate_vote_data(data)
        if not validation_result['valid']:
            return error_response(validation_result['errors'], 400)
        
        firebase_service = current_app.firebase_service
        result = firebase_service.vote_complaint(
            complaint_id=complaint_id,
            user_id=data['user_id'],
            vote_type=data['vote_type']
        )
        
        if result['success']:
            return success_response({
                'message': result['message'],
                'complaint_id': complaint_id,
                'vote_type': data['vote_type'],
                'user_id': data['user_id']
            })
        else:
            return error_response(result['message'], 400)
        
    except Exception as e:
        return error_response(f"Voting failed: {str(e)}", 500)

# =================== SYSTEM INFORMATION ===================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Comprehensive system health check"""
    try:
        firebase_service = current_app.firebase_service
        stats = firebase_service.get_queue_stats()
        
        # Check if complaint processor is running
        processor_status = "running" if hasattr(current_app, 'complaint_processor') else "not_initialized"
        
        return success_response({
            'api_status': 'healthy',
            'firebase_status': 'connected',
            'llm_processor_status': processor_status,
            'queue_statistics': stats.get('queue', {}),
            'complaint_statistics': stats.get('complaints', {}),
            'system_info': {
                'version': '1.0',
                'collections_active': stats.get('system', {}).get('collections_active', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return error_response(f"Health check failed: {str(e)}", 500)

@api_bp.route('/stats', methods=['GET'])
def get_comprehensive_stats():
    """Get comprehensive system and complaint statistics"""
    try:
        firebase_service = current_app.firebase_service
        stats = firebase_service.get_queue_stats()
        
        # Get category breakdown
        categories = ['infrastructure', 'academic', 'hostel']
        category_stats = {}
        
        for category in categories:
            category_complaints = firebase_service.get_complaints_by_category(category)
            category_stats[category] = len(category_complaints)
        
        return success_response({
            'queue_status': stats.get('queue', {}),
            'complaint_counts': {
                'by_visibility': stats.get('complaints', {}),
                'by_category': category_stats
            },
            'system_health': stats.get('system', {}),
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return error_response(f"Statistics unavailable: {str(e)}", 500)

@api_bp.route('/departments', methods=['GET'])
def get_departments():
    """Get list of available departments"""
    departments = [
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
    
    return success_response({
        'departments': departments,
        'total_count': len(departments)
    })

# =================== ADMIN ENDPOINTS (Optional) ===================

@api_bp.route('/admin/queue', methods=['GET'])
def get_queue_details():
    """Get detailed queue information (admin only)"""
    try:
        firebase_service = current_app.firebase_service
        
        # This would require admin authentication in production
        # For now, returning basic queue stats
        stats = firebase_service.get_queue_stats()
        
        return success_response({
            'queue_details': stats,
            'note': 'This endpoint should require admin authentication in production'
        })
        
    except Exception as e:
        return error_response(f"Queue details unavailable: {str(e)}", 500)
