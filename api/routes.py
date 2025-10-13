from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import base64
import io
from PIL import Image

from api.models import AnonymousComplaintSubmission
from api.utils.response_formatter import success_response, error_response
from api.utils.validators import validate_anonymous_complaint_submission

api_bp = Blueprint('api', __name__)

# =================== ANONYMOUS COMPLAINT SUBMISSION ===================

@api_bp.route('/complaints', methods=['POST'])
def submit_anonymous_complaint():
    """
    Submit pseudo-anonymous complaint for LLM processing
    
    Expected JSON:
    {
        "complaint_text": "Raw complaint text...",
        "user_department": "Computer Science & Engineering",
        "user_residence": "Hostel A", // optional
        "user_email": "student@college.edu", // optional for anonymity
        "image_data": "base64_encoded_image" // optional
    }
    """
    try:
        data = request.get_json()
        
        # Validate input data
        validation_result = validate_anonymous_complaint_submission(data)
        if not validation_result['valid']:
            return error_response(validation_result['errors'], 400)
        
        # Handle image validation if present
        if data.get('image_data'):
            try:
                img_binary = base64.b64decode(data['image_data'])
                Image.open(io.BytesIO(img_binary))
            except Exception as e:
                return error_response(f"Invalid image data: {str(e)}", 400)
        
        # Create anonymous complaint submission
        submission = AnonymousComplaintSubmission(
            complaint_text=data['complaint_text'],
            user_department=data['user_department'],
            user_residence=data.get('user_residence'),
            user_email=data.get('user_email'),
            image_data=data.get('image_data')
        )
        
        # Submit to Firebase queue for LLM processing
        firebase_service = current_app.firebase_service
        complaint_id, queue_position = firebase_service.submit_raw_complaint(submission)
        
        # Calculate estimated processing time
        estimated_minutes = queue_position * 1.5  # 1.5 minutes per complaint
        
        return success_response({
            'complaint_id': complaint_id,
            'status': 'queued_for_llm_processing',
            'queue_position': queue_position,
            'estimated_processing_time_minutes': estimated_minutes,
            'message': 'Raw complaint submitted successfully for LLM processing',
            'llm_processing_includes': [
                'Professional rephrasing of your complaint',
                'Intelligent visibility determination (public/private/confidential)',
                'Automatic category classification',
                'Smart routing to appropriate authority'
            ],
            'next_steps': [
                'LLM will analyze and professionally rephrase your complaint',
                'System will determine appropriate visibility level',
                'Complaint will be routed to correct authority',
                'Check status using the complaint_id provided'
            ]
        }, 201)
        
    except Exception as e:
        return error_response(f"Submission failed: {str(e)}", 500)

# =================== COMPLAINT STATUS & RETRIEVAL ===================

@api_bp.route('/complaints/<complaint_id>/status', methods=['GET'])
def get_complaint_status(complaint_id):
    """Get detailed complaint status including LLM processing results"""
    try:
        firebase_service = current_app.firebase_service
        complaint_data = firebase_service.get_complaint_status(complaint_id)
        
        if not complaint_data:
            return error_response("Complaint not found", 404)
        
        # Enhance response with processing stage information
        location = complaint_data.get('location', 'unknown')
        
        if location == 'queue':
            stage_info = {
                'processing_stage': 'In LLM Queue',
                'description': 'Waiting for intelligent LLM processing',
                'current_status': complaint_data.get('status', 'pending'),
                'llm_will_process': [
                    'Professional rephrasing',
                    'Visibility determination',
                    'Category classification',
                    'Authority routing'
                ]
            }
        elif location == 'public':
            stage_info = {
                'processing_stage': 'LLM Processed - Public',
                'description': 'LLM determined this complaint as public for community voting',
                'current_status': 'public_voting_enabled',
                'upvotes': complaint_data.get('upvotes', 0),
                'downvotes': complaint_data.get('downvotes', 0),
                'rephrased_by_llm': True
            }
        elif location == 'private':
            stage_info = {
                'processing_stage': 'LLM Processed - Private',
                'description': 'LLM determined this complaint requires private handling',
                'current_status': 'privately_processed',
                'rephrased_by_llm': True,
                'visibility_reason': 'LLM detected sensitive/personal content'
            }
        else:
            stage_info = {
                'processing_stage': 'Processed',
                'description': 'Complaint has been processed by LLM',
                'current_status': 'completed'
            }
        
        # Add LLM processing information if available
        if complaint_data.get('rephrased_complaint'):
            stage_info['llm_rephrasing'] = {
                'original_length': len(complaint_data.get('original_complaint', '')),
                'rephrased_length': len(complaint_data.get('rephrased_complaint', '')),
                'model_used': complaint_data.get('model_used', 'Unknown')
            }
        
        response_data = {
            **complaint_data,
            'stage_info': stage_info
        }
        
        return success_response(response_data)
        
    except Exception as e:
        return error_response(f"Status retrieval failed: {str(e)}", 500)

@api_bp.route('/complaints/public', methods=['GET'])
def get_public_complaints():
    """Get public complaints that were determined by LLM for community voting"""
    try:
        category = request.args.get('category')
        limit = min(int(request.args.get('limit', 50)), 100)
        
        firebase_service = current_app.firebase_service
        complaints = firebase_service.get_public_complaints(category, limit)
        
        return success_response({
            'complaints': complaints,
            'total_returned': len(complaints),
            'category_filter': category,
            'limit_applied': limit,
            'note': 'All complaints shown were intelligently determined as public by LLM',
            'available_categories': ['infrastructure', 'academic', 'hostel']
        })
        
    except Exception as e:
        return error_response(f"Public complaints retrieval failed: {str(e)}", 500)

@api_bp.route('/complaints/categories/<category>', methods=['GET'])
def get_complaints_by_llm_category(category):
    """Get complaints by LLM-determined category"""
    try:
        if category not in ['infrastructure', 'academic', 'hostel']:
            return error_response(
                "Invalid category. Must be one of: infrastructure, academic, hostel", 
                400
            )
        
        limit = min(int(request.args.get('limit', 50)), 100)
        
        firebase_service = current_app.firebase_service
        complaints = firebase_service.get_complaints_by_category(category, limit)
        
        return success_response({
            'category': category,
            'complaints': complaints,
            'total_found': len(complaints),
            'note': f'All {category} complaints were classified by LLM intelligence'
        })
        
    except Exception as e:
        return error_response(f"Category retrieval failed: {str(e)}", 500)

# =================== VOTING SYSTEM (Public Complaints Only) ===================

@api_bp.route('/complaints/<complaint_id>/vote', methods=['POST'])
def vote_on_public_complaint(complaint_id):
    """
    Vote on LLM-determined public complaints
    
    Expected JSON:
    {
        "user_id": "anonymous_user_123",
        "vote_type": "upvote" // upvote or downvote
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'vote_type' not in data or 'user_id' not in data:
            return error_response("Missing vote_type or user_id", 400)
        
        if data['vote_type'] not in ['upvote', 'downvote']:
            return error_response("vote_type must be 'upvote' or 'downvote'", 400)
        
        firebase_service = current_app.firebase_service
        result = firebase_service.vote_on_public_complaint(
            complaint_id=complaint_id,
            user_id=data['user_id'],
            vote_type=data['vote_type']
        )
        
        if result['success']:
            return success_response({
                'message': result['message'],
                'complaint_id': complaint_id,
                'vote_type': data['vote_type'],
                'user_id': data['user_id'],
                'note': 'Vote recorded on LLM-determined public complaint'
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
        stats = firebase_service.get_system_statistics()
        
        # Check if LLM processor is running
        processor_status = "running" if hasattr(current_app, 'complaint_processor') else "not_initialized"
        
        return success_response({
            'api_status': 'healthy',
            'firebase_status': 'connected',
            'llm_processor_status': processor_status,
            'system_type': 'pseudo_anonymous_with_llm_intelligence',
            'queue_statistics': stats.get('queue_status', {}),
            'processing_statistics': stats.get('processed_complaints', {}),
            'llm_capabilities': [
                'Professional complaint rephrasing',
                'Intelligent visibility determination',
                'Automatic category classification',
                'Smart authority routing'
            ],
            'privacy_features': [
                'Email-only pseudo-anonymity',
                'LLM-determined visibility levels',
                'Automatic sensitive content detection'
            ],
            'system_info': {
                'version': '2.0',
                'last_updated': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        return error_response(f"Health check failed: {str(e)}", 500)

@api_bp.route('/stats', methods=['GET'])
def get_comprehensive_stats():
    """Get comprehensive system and LLM processing statistics"""
    try:
        firebase_service = current_app.firebase_service
        stats = firebase_service.get_system_statistics()
        
        return success_response({
            'queue_status': stats.get('queue_status', {}),
            'processing_breakdown': stats.get('processed_complaints', {}),
            'system_health': stats.get('system_health', {}),
            'llm_processing_info': {
                'total_llm_processed': stats.get('processed_complaints', {}).get('total_processed', 0),
                'public_determinations': stats.get('processed_complaints', {}).get('public_complaints', 0),
                'private_determinations': stats.get('processed_complaints', {}).get('private_complaints', 0)
            },
            'anonymity_stats': {
                'pseudo_anonymous_system': True,
                'email_only_identification': True,
                'llm_visibility_determination': True
            },
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return error_response(f"Statistics unavailable: {str(e)}", 500)

@api_bp.route('/departments', methods=['GET'])
def get_departments():
    """Get list of available departments for complaint submission"""
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
        'total_count': len(departments),
        'note': 'Select your department for accurate complaint routing'
    })

# =================== LLM PROCESSING INFO ===================

@api_bp.route('/llm/capabilities', methods=['GET'])
def get_llm_capabilities():
    """Get information about LLM processing capabilities"""
    return success_response({
        'llm_processing_features': {
            'professional_rephrasing': {
                'description': 'Converts casual complaints into formal, professional language',
                'benefit': 'Ensures appropriate tone for official submission'
            },
            'intelligent_visibility_determination': {
                'description': 'Automatically determines if complaint should be public, private, or confidential',
                'levels': {
                    'public': 'General issues suitable for community voting',
                    'private': 'Personal matters requiring administrative discretion',
                    'confidential': 'Sensitive issues needing highest security'
                }
            },
            'smart_categorization': {
                'description': 'Accurately classifies complaints into appropriate categories',
                'categories': ['academic', 'hostel', 'infrastructure']
            },
            'authority_routing': {
                'description': 'Routes complaints to most appropriate authority based on content',
                'ensures': 'Faster resolution by reaching right person immediately'
            }
        },
        'privacy_protection': {
            'pseudo_anonymity': 'Email-only identification for accountability with privacy',
            'sensitive_detection': 'Automatic identification of sensitive content',
            'secure_handling': 'Appropriate visibility levels for different complaint types'
        },
        'quality_assurance': {
            'professional_tone': 'All complaints converted to appropriate formal language',
            'consistent_formatting': 'Standardized complaint structure for efficient processing',
            'intelligent_routing': 'Reduced processing time through smart authority matching'
        }
    })
