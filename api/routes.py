from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import base64
import io
from PIL import Image

# Import local modules (no circular imports)
from api.models import ComplaintSubmissionModel, VoteModel
from api.utils.response_formatter import success_response, error_response
from api.utils.validators import validate_complaint_data

api_bp = Blueprint('api', __name__)

@api_bp.route('/complaints', methods=['POST'])
def submit_complaint():
    """Submit a new complaint - queued for LLM processing"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validation_result = validate_complaint_data(data)
        if not validation_result['valid']:
            return error_response(validation_result['errors'], 400)
        
        # Handle image if present
        image_data = None
        if 'image' in data and data['image']:
            try:
                image_data = data['image']
                img_binary = base64.b64decode(image_data)
                Image.open(io.BytesIO(img_binary))
            except Exception as e:
                return error_response(f"Invalid image data: {str(e)}", 400)
        
        # Create complaint model
        complaint = ComplaintSubmissionModel(
            complaint_text=data['complaint_text'],
            user_department=data['user_department'],
            user_residence=data.get('user_residence'),
            user_email=data.get('user_email'),
            user_phone=data.get('user_phone'),
            image_data=image_data,
            privacy_level=data.get('privacy_level', 'public')
        )
        
        # Save to Firebase
        firebase_service = current_app.firebase_service
        complaint_id = firebase_service.save_complaint(complaint.to_dict())
        
        # Add to processing queue
        queue_manager = current_app.queue_manager
        queue_position = queue_manager.add_to_queue(complaint_id, complaint.to_dict())
        
        return success_response({
            'complaint_id': complaint_id,
            'status': 'queued',
            'queue_position': queue_position,
            'message': 'Complaint submitted successfully and queued for processing'
        }, 201)
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)

@api_bp.route('/complaints/<complaint_id>/status', methods=['GET'])
def get_complaint_status(complaint_id):
    """Get complaint status and processing results"""
    try:
        firebase_service = current_app.firebase_service
        complaint_data = firebase_service.get_complaint_status(complaint_id)
        
        if not complaint_data:
            return error_response("Complaint not found", 404)
        
        # Get queue status if still pending
        if complaint_data['status'] == 'pending':
            queue_manager = current_app.queue_manager
            queue_info = queue_manager.get_queue_position(complaint_id)
            complaint_data.update(queue_info)
        
        return success_response(complaint_data)
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)

@api_bp.route('/complaints/public', methods=['GET'])
def get_public_complaints():
    """Get public complaints for upvoting/downvoting"""
    try:
        category = request.args.get('category')  # infrastructure, academic, hostel
        limit = min(int(request.args.get('limit', 50)), 100)
        
        firebase_service = current_app.firebase_service
        complaints = firebase_service.get_public_complaints(category, limit)
        
        return success_response({
            'complaints': complaints,
            'total': len(complaints),
            'category_filter': category
        })
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)

@api_bp.route('/complaints/<complaint_id>/vote', methods=['POST'])
def vote_complaint(complaint_id):
    """Upvote or downvote a public complaint"""
    try:
        data = request.get_json()
        
        if not data or 'vote_type' not in data or 'user_id' not in data:
            return error_response("Missing vote_type or user_id", 400)
        
        if data['vote_type'] not in ['upvote', 'downvote']:
            return error_response("vote_type must be 'upvote' or 'downvote'", 400)
        
        firebase_service = current_app.firebase_service
        result = firebase_service.vote_complaint(
            complaint_id=complaint_id,
            user_id=data['user_id'],
            vote_type=data['vote_type']
        )
        
        if result['success']:
            return success_response(result)
        else:
            return error_response(result['message'], 400)
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)

@api_bp.route('/complaints/categories/<category>', methods=['GET'])
def get_complaints_by_category(category):
    """Get complaints filtered by category (infrastructure/academic/hostel)"""
    try:
        if category not in ['infrastructure', 'academic', 'hostel']:
            return error_response("Invalid category. Must be: infrastructure, academic, or hostel", 400)
        
        limit = min(int(request.args.get('limit', 50)), 100)
        
        firebase_service = current_app.firebase_service
        complaints = firebase_service.get_public_complaints(category, limit)
        
        return success_response({
            'category': category,
            'complaints': complaints,
            'total': len(complaints)
        })
        
    except Exception as e:
        return error_response(f"Internal server error: {str(e)}", 500)

@api_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    try:
        queue_manager = current_app.queue_manager
        queue_stats = queue_manager.get_queue_stats()
        
        return success_response({
            'status': 'healthy',
            'queue_stats': queue_stats,
            'timestamp': str(datetime.utcnow())
        })
    except Exception as e:
        return error_response(f"Health check failed: {str(e)}", 500)
