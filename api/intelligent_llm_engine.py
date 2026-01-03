"""
Intelligent LLM Engine - CampusVoice Complaint System
Version: 4.0.0 - Production Ready
GROQ-POWERED with Full Integration

Complete complaint processing pipeline:
- LLM-based categorization & rephrasing
- Authority routing (via AuthorityMapper)
- Priority scoring (via PriorityScorer)
- Authority conflict detection
- Smart image detection
- Visibility determination
- Retry logic with exponential backoff
"""

import json
import re
import time
import hashlib
from typing import Optional, Dict, Any, Tuple, List
from groq import Groq
from datetime import datetime, timezone

from api.models import Complaint, ComplaintSubmission
from core.config import get_config
from core.authority_mapper import AuthorityMapper
from core.priority_scorer import PriorityScorer

# Get configuration
config = get_config()


class IntelligentLLMEngine:
    """
    Advanced LLM engine powered by Groq with complete integration.
    """

    def __init__(self):
        """Initialize LLM engine with Groq and core modules."""
        self.config = config
        
        # Groq configuration
        self.groq_api_key = config.groq_api_key
        self.groq_model = config.groq_model  # llama-3.3-70b-versatile
        
        # Initialize Groq client
        self.groq_available = False
        if self.groq_api_key:
            try:
                self.groq_client = Groq(api_key=self.groq_api_key)
                self.groq_available = True
                print("🚀 Intelligent LLM Engine initialized")
                print(f"   ⚡ Model: {self.groq_model}")
                print("   ✅ Groq API: Connected")
            except Exception as e:
                print(f"   ⚠️ Groq initialization failed: {e}")
                print("   🔄 Falling back to rule-based processing")
        else:
            print("⚠️ No Groq API key found - using rule-based fallback")
        
        # Initialize core modules
        self.authority_mapper = AuthorityMapper(config)
        self.priority_scorer = PriorityScorer(config)
        
        # Import keywords from config instead of hardcoding
        self._initialize_keyword_sets()
        
        print("✅ LLM Engine ready with full integration")

    def _initialize_keyword_sets(self):
        """Initialize keyword sets from config."""
        # Privacy keywords from config
        self.confidential_keywords = config.privacy_keywords
        
        self.private_keywords = [
            'personal', 'individual', 'specific to me', 'my issue', "don't share",
            'between us', 'personally', 'individual case', 'just for me', 'only me'
        ]
        
        # ✅ FIX: Define category_keywords HERE instead of from config
        self.category_keywords = {
            'hostel': [
                'hostel', 'mess', 'room', 'warden', 'deputy warden', 'food', 'wifi',
                'water', 'bathroom', 'cleanliness', 'laundry', 'electricity', 'fan',
                'ac', 'bed', 'dormitory', 'canteen', 'dining', 'hygiene', 'accommodation',
                'roommate', 'noise', 'security', 'entry', 'gate timing', 'curfew',
                'mess hall', 'dining hall', 'hostel wifi', 'hostel room'
            ],
            'academic': [
                'professor', 'faculty', 'teacher', 'class', 'lecture', 'exam', 'test',
                'syllabus', 'curriculum', 'lab', 'laboratory', 'assignment', 'project',
                'marks', 'grades', 'teaching', 'subject', 'course', 'semester', 'practical',
                'theory', 'attendance', 'tutorial', 'evaluation', 'assessment', 'timetable',
                'schedule', 'internal', 'external', 'viva', 'presentation', 'classmate',
                'peer', 'student', 'instructor', 'staff', 'department lab'
            ],
            'infrastructure': [
                'building', 'classroom', 'library', 'auditorium', 'lift', 'elevator',
                'parking', 'ground', 'playground', 'toilet', 'washroom', 'corridor',
                'staircase', 'roof', 'gate', 'security', 'maintenance', 'repair',
                'construction', 'facility', 'equipment', 'furniture', 'lighting',
                'ventilation', 'cleanliness', 'water supply', 'electricity supply',
                'plumbing', 'broken', 'damaged', 'leaking', 'cracked'
            ]
        }
        
        # Try to get dept_aliases from config, fallback to defaults
        try:
            self.dept_alias = {
                "cse": "Computer Science & Engineering",
                "ece": "Electronics & Communication Engineering",
                "it": "Information Technology",
                "eee": "Electrical & Electronics Engineering",
                "ei": "Electronics & Instrumentation Engineering",
                "e&i": "Electronics & Instrumentation Engineering",
                "mechanical": "Mechanical Engineering",
                "mech": "Mechanical Engineering",
                "civil": "Civil Engineering",
                "biomedical": "Biomedical Engineering",
                "aero": "Aeronautical Engineering",
                "ai&ds": "Artificial Intelligence and Data Science",
                "aids": "Artificial Intelligence and Data Science",
                "robotics": "Robotics and Automation",
                "management": "Management Studies"
            }
        except:
            self.dept_alias = {}
        
        # Building/block keywords
        self.building_keywords = [
            'block a', 'block b', 'block c', 'main building', 'admin block',
            'ece block', 'cse block', 'it block', 'mechanical block', 'civil block',
            'library', 'auditorium', 'seminar hall', 'conference hall', 'workshop',
            'canteen building', 'sports complex', 'gymnasium'
        ]
        
        # Context facility keywords
        self.context_facility_keywords = [
            'drinking water', 'water', 'bathroom', 'toilet', 'electricity',
            'power', 'plumbing', 'tap', 'washroom', 'restroom'
        ]
        
        # Department asset keywords
        self.department_asset_keywords = [
            '3d printer', 'oscilloscope', 'cnc', 'lathe', 'soldering',
            'department lab', 'dept lab', 'project lab', 'instrument',
            'instruments', 'equipment', 'laboratory', 'lab equipment'
        ]
        
        # Hostel detection cues
        self.hostel_cues = [
            'hostel', 'warden', 'deputy warden', 'mess',
            'curfew', 'room ', 'hostel room'
        ]
        
        # Image requirement keywords
        self.image_required_keywords = config.image_required_keywords

    # =================== MAIN PROCESSING METHOD ===================

    def process_complaint(
        self,
        submission: ComplaintSubmission,
        complaint_id: str
    ) -> Complaint:
        """
        Complete complaint processing pipeline.
        
        Args:
            submission: ComplaintSubmission object
            complaint_id: Unique complaint identifier
        
        Returns:
            Complete Complaint object with all fields populated
        """
        print(f"🧠 Processing complaint: {complaint_id}")
        start_time = time.time()
        
        try:
            # 1. Hash roll number for pseudo-anonymity
            roll_hash = self._hash_roll_number(submission.roll_number)
            
            # 2. LLM processing (categorization, rephrasing, visibility)
            llm_result = self._process_with_llm(
                submission.complaint_text,
                {
                    'department': submission.department,
                    'gender': submission.gender,
                    'residence': submission.residence,
                    'roll_number': submission.roll_number
                }
            )
            
            # 3. Detect authority conflicts
            conflict = self._detect_authority_conflict(
                submission.complaint_text,
                submission.department
            )
            
            # 4. Authority routing (using AuthorityMapper)
            routing = self.authority_mapper.route_complaint(
                category=llm_result['category'],
                user_department=submission.department,
                complaint_text=submission.complaint_text,
                mentioned_department=llm_result.get('mentioned_department'),
                mentioned_authority=conflict['mentioned_authority'],
                needs_bypass=conflict['needs_bypass'],
                requires_image=llm_result['image_required'],
                image_reason=llm_result.get('image_requirement_reason', '')
            )
            
            # 5. Priority scoring (using PriorityScorer)
            priority = self.priority_scorer.calculate_priority(
                complaint=submission.complaint_text,
                category=llm_result['category'],
                requires_image=llm_result['image_required'],
                is_mandatory_image=llm_result.get('is_mandatory_image', False)
            )
            
            # 6. Determine visibility type
            visibility_type = self._determine_visibility_type(llm_result['visibility'])
            
            # 7. Create complete Complaint object
            complaint = Complaint(
                complaint_id=complaint_id,
                roll_number_hash=roll_hash,
                department=submission.department,
                gender=submission.gender,
                residence=submission.residence,
                original_text=submission.complaint_text,
                rephrased_text=llm_result['rephrased_complaint'],
                category=llm_result['category'],
                assigned_authority=routing['final_authority'],
                routing_path=routing['routing_path'],
                routing_reasoning=routing['routing_reasoning'],
                hidden_from=routing['hidden_from'],
                bypass_applied=routing.get('bypass_applied', False),
                escalated_to=routing.get('escalated_to'),
                priority_level=priority.get('level', 'Medium'),  # ✅ FIXED
                priority_score=priority.get('score', 50.0),  # ✅ FIXED
                priority_breakdown=priority.get('breakdown', []),  # ✅ FIXED
                priority_emoji=priority.get('emoji', '🟡'),  # ✅ FIXED - Default emoji
                status='raised',
                visibility_type=visibility_type,
                is_public=submission.is_public and visibility_type == 'public',
                requires_image=llm_result['image_required'],
                image_requirement_reason=llm_result.get('image_requirement_reason'),
                is_mandatory_image=llm_result.get('is_mandatory_image', False),
                image_urls=[],
                upvotes=0,
                downvotes=0,
                net_votes=0,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                opened_at=None,
                reviewed_at=None,
                closed_at=None,
                status_history=[],
                processing_time=time.time() - start_time,
                llm_model_used=llm_result.get('model_used', 'rule_based_engine'),
                llm_confidence=llm_result.get('confidence', 'Medium'),
                contains_abusive_language=llm_result.get('contains_abusive_language', False),
                language_issues=llm_result.get('language_issues')
            )
            
            # Flag user if abusive language detected
            if complaint.contains_abusive_language:
                self._flag_abusive_user(submission.roll_number, complaint.complaint_id)
            
            print(f"✅ Processing completed in {complaint.processing_time:.2f}s")
            return complaint
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
            # Return minimal complaint with error handling
            return self._create_fallback_complaint(
                submission,
                complaint_id,
                start_time,
                str(e)
            )

    # =================== LLM PROCESSING ===================

    def _process_with_llm(
        self,
        complaint_text: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process complaint with LLM (with retry logic).
        
        Returns:
            Dict with rephrased_complaint, visibility, category, etc.
        """
        if self.groq_available:
            try:
                print(f"   ⚡ Using Groq ({self.groq_model})")
                result = self._groq_with_retry(complaint_text, user_context)
            except Exception as e:
                print(f"   ⚠️ Groq failed, using fallback: {e}")
                result = self._rule_based_complete_processing(complaint_text, user_context)
        else:
            print("   🔧 Using rule-based fallback")
            result = self._rule_based_complete_processing(complaint_text, user_context)
        
        # Extract routing hints
        hints = self._extract_routing_hints(complaint_text, user_context)
        result.update(hints)
        
        # Preserve referenced department/block in rephrasing
        result['rephrased_complaint'] = self._preserve_reference_in_rephrase(
            original=complaint_text,
            rephrased=result.get('rephrased_complaint', ''),
            hints=hints
        )
        
        # Context-aware category determination
        result['category'] = self._context_aware_category(
            complaint_text,
            user_context,
            preferred=result.get('category')
        )
        
        # Sensitive content handling
        if self._has_confidential_content(complaint_text):
            result['visibility'] = 'confidential'
            if self._is_refusal_or_empty(result.get('rephrased_complaint', '')):
                result['rephrased_complaint'] = self._default_sensitive_text(user_context)
        
        # Image detection
        needs_image, reason, is_mandatory = self.check_if_image_needed(complaint_text)
        result['image_required'] = needs_image
        result['image_requirement_reason'] = reason
        result['is_mandatory_image'] = is_mandatory
        
        # Location clarity check
        if self._is_location_unclear(complaint_text):
            result['needs_clarification'] = True
            result['visibility'] = 'private'
            result['category'] = 'infrastructure'
            result['confidence'] = 'Low'
            result['rephrased_complaint'] = (
                "Please include the exact location (Hostel name/room, "
                "Block/Classroom, or Department/Lab) for proper routing."
            )
        
        return result

    def _groq_with_retry(
        self,
        complaint: str,
        user_context: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Call Groq API with exponential backoff retry."""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self._groq_complete_processing(complaint, user_context)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"   ⏳ Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
        
        # If all retries failed, raise the last error
        raise last_error

    def _groq_complete_processing(
        self,
        complaint: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process complaint using Groq API."""
        system_prompt = """You are Campus Voice AI, an intelligent complaint processing system for a college campus.
Your task is to analyze complaints and provide structured output in JSON format.

User Context Schema:
- roll_number: Student identifier for accountability
- gender: male/female/other
- department: Student's department
- residence: Hostel name or "Day Scholar"

Processing Tasks:
1. REPHRASE the complaint professionally (1-2 sentences, formal tone, preserve specific details)
   - Remove ALL abusive language, profanity, and informal slang
   - Convert to formal, respectful language
   - Preserve the core meaning and specific details
   - Flag if original text contained abusive/violent language
2. DETERMINE visibility level (see rules below)
3. CLASSIFY category (see rules below)
4. PROVIDE brief reasoning

Language Processing Rules:
- Detect abusive, profane, or very informal language
- Convert to formal, professional tone
- Remove all bad words and replace with appropriate formal alternatives
- Flag abusive/violent language for user tracking

Visibility Rules:
- CONFIDENTIAL: Harassment, abuse, sexual misconduct, discrimination, mental health issues, ragging, very personal issues
- PRIVATE: Personal issues, individual cases, requests for anonymity, student specifically asks not to share
- PUBLIC: General issues affecting multiple students (default for infrastructure/academic issues)

Category Rules:
- HOSTEL: Mess, hostel rooms, warden issues, hostel facilities, hostel WiFi, hostel water/bathroom
- ACADEMIC: Teaching, faculty, exams, labs, department equipment, academic misconduct, curriculum
- INFRASTRUCTURE: Buildings, classrooms, general facilities, non-hostel bathrooms, campus infrastructure

Special Rules:
- Classroom issues → ALWAYS infrastructure
- Department lab equipment (3D printer, oscilloscope, etc.) → academic
- Buildings/blocks → infrastructure (unless department-specific equipment)
- Hostel-related facilities (mess, hostel rooms) → hostel
- Sensitive content (harassment, abuse, ragging, very personal issues) → ALWAYS confidential
- Faculty/teaching complaints → academic

Response Format (MUST be valid JSON):
{
  "rephrased_complaint": "Professional formal version of the complaint (no bad words, formal tone)",
  "visibility": "public|private|confidential",
  "category": "hostel|academic|infrastructure",
  "confidence": "High|Medium|Low",
  "reasoning": "Brief explanation of classification",
  "contains_abusive_language": true/false,
  "language_issues": "Description of language issues found (if any)"
}"""

        user_prompt = f"""Original Complaint: {complaint}

User Context:
- roll_number: {user_context.get('roll_number', 'unknown')}
- gender: {user_context.get('gender', 'unknown')}
- department: {user_context.get('department', 'unknown')}
- residence: {user_context.get('residence', 'unknown')}

Process this complaint and return ONLY valid JSON."""

        try:
            # Call Groq API
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.15,
                max_tokens=500,
                top_p=0.9
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                llm_result = json.loads(json_match.group())
                
                # Validate and sanitize response
                llm_result = self._validate_llm_output(llm_result)
                
                # Detect abusive language (rule-based fallback if LLM didn't detect)
                if not llm_result.get('contains_abusive_language', False):
                    llm_result['contains_abusive_language'] = self._detect_abusive_language(complaint)
                    if llm_result['contains_abusive_language']:
                        llm_result['language_issues'] = "Informal or inappropriate language detected"
                
                # Override for confidential content
                if self._has_confidential_content(complaint):
                    llm_result['visibility'] = 'confidential'
                
                # Handle refusals
                if self._is_refusal_or_empty(llm_result.get('rephrased_complaint', '')):
                    llm_result['rephrased_complaint'] = self._default_sensitive_text(user_context)
                
                # Ensure rephrased text is formal (rule-based cleanup)
                if llm_result.get('contains_abusive_language', False):
                    llm_result['rephrased_complaint'] = self._formalize_text(
                        llm_result.get('rephrased_complaint', complaint)
                    )
                
                llm_result['model_used'] = self.groq_model
                print("   ✅ Groq processing successful")
                return llm_result
            else:
                print("   ⚠️ No JSON found in Groq response")
                return self._parse_llm_text_response(response_text, complaint, user_context)
                
        except Exception as e:
            print(f"   ❌ Groq API error: {e}")
            raise

    def _validate_llm_output(self, llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize LLM output."""
        # Validate visibility
        if llm_result.get('visibility') not in ['public', 'private', 'confidential']:
            llm_result['visibility'] = 'public'
        
        # Validate category
        if llm_result.get('category') not in ['hostel', 'academic', 'infrastructure']:
            llm_result['category'] = 'infrastructure'
        
        # Validate confidence
        if llm_result.get('confidence') not in ['High', 'Medium', 'Low']:
            llm_result['confidence'] = 'Medium'
        
        # Ensure rephrased_complaint exists
        if not llm_result.get('rephrased_complaint'):
            llm_result['rephrased_complaint'] = 'Complaint requires review.'
        
        return llm_result

    def _parse_llm_text_response(
        self,
        response_text: str,
        original_complaint: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse non-JSON LLM response."""
        lines = response_text.split('\n')
        rephrased = ""
        
        # Find the rephrased text
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:
                if not line.lower().startswith(('visibility:', 'category:', 'confidence:')):
                    rephrased = line
                    break
        
        if not rephrased:
            rephrased = self._rule_based_rephrase(original_complaint, user_context)
        
        # Extract visibility and category from text
        rl = response_text.lower()
        visibility = 'public'
        if 'confidential' in rl:
            visibility = 'confidential'
        elif 'private' in rl:
            visibility = 'private'
        
        category = self._rule_based_classify_category(original_complaint)
        if 'hostel' in rl:
            category = 'hostel'
        elif any(k in rl for k in ['academic', 'professor', 'lab']):
            category = 'academic'
        
        return {
            'rephrased_complaint': rephrased,
            'visibility': visibility,
            'category': category,
            'confidence': 'Medium',
            'reasoning': 'Parsed from LLM text response',
            'model_used': self.groq_model
        }

    # =================== SMART IMAGE DETECTION ===================

    def check_if_image_needed(self, complaint: str) -> Tuple[bool, str, bool]:
        """
        Intelligently determine if complaint needs an image.
        
        Args:
            complaint: Raw complaint text
        
        Returns:
            Tuple of (needs_image: bool, reason: str, is_mandatory: bool)
        """
        txt = complaint.lower()
        
        # Mandatory image keywords (critical for resolution)
        mandatory_keywords = ['broken', 'damaged', 'cracked', 'leaking', 'torn']
        for keyword in mandatory_keywords:
            if keyword in txt:
                return (
                    True,
                    f"Visual evidence required for '{keyword}' complaints to enable proper assessment and resolution",
                    True  # Mandatory
                )
        
        # Recommended image keywords
        for keyword in self.image_required_keywords:
            if keyword in txt:
                return (
                    True,
                    f"Visual evidence recommended for '{keyword}' complaints to enable faster resolution",
                    False  # Recommended but not mandatory
                )
        
        # Infrastructure issues often benefit from images
        if any(kw in txt for kw in ['leak', 'crack', 'damage']):
            return (
                True,
                "Infrastructure damage complaints are resolved faster with visual evidence",
                False
            )
        
        # Use Groq for intelligent detection if available
        if self.groq_available:
            try:
                needs_image, reason = self._groq_image_detection(complaint)
                return (needs_image, reason, False)
            except:
                pass  # Fallback to rule-based
        
        # Default: no image needed
        return (False, "Text description is sufficient for this type of complaint", False)

    def _groq_image_detection(self, complaint: str) -> Tuple[bool, str]:
        """Use Groq to intelligently detect if image is needed."""
        prompt = f"""Analyze this college complaint and determine if a photo/image would help resolve it faster.

Complaint: {complaint}

Respond with JSON only:
{{
  "needs_image": true/false,
  "reason": "Brief explanation why image is/isn't needed"
}}

Image is useful for: Physical damage, broken equipment, cleanliness issues, infrastructure problems.
Image NOT needed for: Policy complaints, teaching issues, abstract concerns."""

        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150
            )
            
            response_text = response.choices[0].message.content.strip()
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                return (result.get('needs_image', False), result.get('reason', ''))
        
        except Exception as e:
            print(f"   ⚠️ Groq image detection failed: {e}")
        
        # Fallback
        return (False, "Image detection unavailable - proceeding with text only")

    # =================== AUTHORITY CONFLICT DETECTION ===================

    def _detect_authority_conflict(
        self,
        complaint: str,
        user_department: str
    ) -> Dict[str, Any]:
        """
        Detect if complaint is AGAINST an authority figure.
        
        Returns:
            Dict with:
            - mentioned_authority: str (hod/faculty/warden/ao/principal/deputy_warden/none)
            - needs_bypass: bool
            - authority_name: Optional[str] (extracted name if mentioned)
        """
        txt = complaint.lower()
        
        result = {
            'mentioned_authority': 'none',
            'needs_bypass': False,
            'authority_name': None
        }
        
        # Check for authority mentions with negative context
        negative_indicators = [
            'not responding', 'not helping', 'not listening', 'ignoring',
            'refuses to', 'refusing to', 'denied', 'denying', 'unfair',
            'biased', 'partial', 'harassment', 'misbehav', 'rude',
            'inappropriate', 'unprofessional', 'complaint against'
        ]
        
        has_negative = any(indicator in txt for indicator in negative_indicators)
        
        # Authority detection
        if 'principal' in txt and has_negative:
            result['mentioned_authority'] = 'principal'
            result['needs_bypass'] = True  # Escalate to higher committee
        
        elif any(term in txt for term in ['head of department', 'hod', 'dept head']):
            if has_negative:
                result['mentioned_authority'] = 'hod'
                result['needs_bypass'] = True  # Bypass to Principal
        
        elif any(term in txt for term in ['senior deputy warden', 'sdw']):
            if has_negative:
                result['mentioned_authority'] = 'senior_deputy_warden'
                result['needs_bypass'] = True  # Bypass to Principal
        
        elif 'deputy warden' in txt or 'dw ' in txt:
            if has_negative:
                result['mentioned_authority'] = 'deputy_warden'
                result['needs_bypass'] = True  # Escalate to Senior Deputy Warden
        
        elif 'warden' in txt and 'deputy' not in txt:
            if has_negative:
                result['mentioned_authority'] = 'warden'
                result['needs_bypass'] = True  # Escalate to Senior Deputy Warden
        
        elif any(term in txt for term in ['administrative officer', 'ao ', 'admin officer']):
            if has_negative:
                result['mentioned_authority'] = 'ao'
                result['needs_bypass'] = True  # Bypass to Principal
        
        elif any(term in txt for term in ['professor', 'faculty', 'teacher', 'lecturer', 'instructor']):
            if has_negative:
                result['mentioned_authority'] = 'faculty'
                result['needs_bypass'] = True  # Bypass to HOD
                # Try to extract faculty name
                result['authority_name'] = self._extract_faculty_name(complaint)
        
        return result

    def _extract_faculty_name(self, complaint: str) -> Optional[str]:
        """Extract faculty name from complaint (basic pattern matching)."""
        # Look for patterns like "Prof. Name", "Dr. Name", "Mr./Mrs./Ms. Name"
        patterns = [
            r'(?:Prof|Professor|Dr|Mr|Mrs|Ms)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'faculty\s+(?:member\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, complaint)
            if match:
                return match.group(1).strip()
        
        return None

    # =================== RULE-BASED PROCESSING ===================

    def _rule_based_complete_processing(
        self,
        complaint: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Intelligent rule-based processing (fallback)."""
        print("   🔧 Using intelligent rule-based engine")
        
        visibility = self._determine_visibility_rules(complaint)
        category = self._rule_based_classify_category(complaint)
        
        # Detect abusive language
        contains_abusive = self._detect_abusive_language(complaint)
        
        # Rephrase with formalization if needed
        rephrased = self._rule_based_rephrase(complaint, user_context)
        if contains_abusive:
            rephrased = self._formalize_text(rephrased)
        
        # Override for confidential content
        if self._has_confidential_content(complaint):
            visibility = 'confidential'
            if self._is_refusal_or_empty(rephrased):
                rephrased = self._default_sensitive_text(user_context)
        
        return {
            'rephrased_complaint': rephrased,
            'visibility': visibility,
            'category': category,
            'confidence': 'High' if visibility == 'confidential' else 'Medium',
            'reasoning': f'Rule-based: {category} complaint, {visibility} visibility',
            'model_used': 'rule_based_engine',
            'contains_abusive_language': contains_abusive,
            'language_issues': "Informal or inappropriate language detected" if contains_abusive else None
        }

    def _determine_visibility_rules(self, complaint: str) -> str:
        """Determine visibility using rules."""
        txt = complaint.lower()
        
        # Confidential check
        if self._has_confidential_content(txt):
            return 'confidential'
        
        # Private keywords
        for kw in self.private_keywords:
            if kw in txt:
                return 'private'
        
        # Personal indicators
        indicators = ['my ', 'i am', 'i have', 'i was', 'personally', 'individual']
        if sum(1 for i in indicators if i in txt) >= 2:
            return 'private'
        
        return 'public'

    def _has_confidential_content(self, complaint: str) -> bool:
        """Check for confidential content."""
        txt = complaint.lower()
        return any(kw in txt for kw in self.confidential_keywords)

    def _rule_based_classify_category(self, complaint: str) -> str:
        """Classify category using rules."""
        txt = complaint.lower()
        
        # Buildings/blocks always infrastructure (unless dept asset)
        for b in self.building_keywords:
            if b in txt:
                return 'infrastructure'
        
        # Score each category
        scores = {k: 0 for k in self.category_keywords}
        for cat, kws in self.category_keywords.items():
            for kw in kws:
                if kw in txt:
                    scores[cat] += 1
        
        # Boost scores for specific indicators
        if any(w in txt for w in ['warden', 'deputy warden']):
            scores['hostel'] += 5
        
        if any(w in txt for w in ['professor', 'faculty', 'teaching', 'lab']):
            scores['academic'] += 5
        
        if any(w in txt for w in ['building', 'facility', 'maintenance']):
            scores['infrastructure'] += 3
        
        # Get category with highest score
        max_cat = max(scores, key=scores.get)
        
        # Default categorization if no matches
        if scores[max_cat] == 0:
            if any(w in txt for w in ['room', 'mess', 'food']):
                return 'hostel'
            if any(w in txt for w in ['class', 'exam', 'study']):
                return 'academic'
            return 'infrastructure'
        
        return max_cat

    def _context_aware_category(
        self,
        complaint: str,
        user_context: Dict[str, Any],
        preferred: Optional[str]
    ) -> str:
        """Context-aware category determination with smart rules."""
        txt = complaint.lower()
        
        # Confidential content goes to academic (disciplinary)
        if self._has_confidential_content(txt):
            return 'academic'
        
        # Classroom is always infrastructure
        if 'classroom' in txt or 'class room' in txt:
            return 'infrastructure'
        
        # Department assets are academic
        if any(k in txt for k in self.department_asset_keywords):
            return 'academic'
        
        # Buildings/blocks are infrastructure
        if any(b in txt for b in self.building_keywords):
            return 'infrastructure'
        
        # Facilities require hostel cues to be hostel
        if any(k in txt for k in self.context_facility_keywords):
            if any(h in txt for h in self.hostel_cues):
                return 'hostel'
            return 'infrastructure'
        
        return preferred or self._rule_based_classify_category(complaint)

    def _rule_based_rephrase(self, complaint: str, user_context: Dict[str, Any]) -> str:
        """Rephrase complaint using rules."""
        # Handle confidential content
        if self._has_confidential_content(complaint):
            return self._default_sensitive_text(user_context)
        
        # Check for abusive language and formalize
        contains_abusive = self._detect_abusive_language(complaint)
        rephrased = self._formalize_text(complaint.strip()) if contains_abusive else complaint.strip()
        
        # Add professional opening if needed
        if not rephrased.startswith(("I would like", "We would like", "This is", "I am")):
            cat = self._context_aware_category(
                complaint,
                user_context,
                preferred=self._rule_based_classify_category(complaint)
            )
            
            openings = {
                'hostel': "I would like to bring to your attention a hostel-related concern. ",
                'academic': "I am writing to address an academic matter that requires attention. ",
                'infrastructure': "This is to report an infrastructure issue that needs resolution. "
            }
            
            rephrased = openings.get(cat, "") + rephrased
        
        # Professional replacements
        replacements = {
            " really ": " significantly ",
            " very ": " considerably ",
            " bad ": " inadequate ",
            " terrible ": " unsatisfactory ",
            " can't ": " cannot ",
            " won't ": " will not ",
            " don't ": " do not ",
            " isn't ": " is not ",
            " doesn't ": " does not ",
            " gonna ": " going to ",
            " wanna ": " want to "
        }
        
        for old, new in replacements.items():
            rephrased = rephrased.replace(old, new)
        
        # Ensure proper ending
        if not rephrased.endswith('.'):
            rephrased += "."
        
        # Add closing if short
        if len(rephrased) < 100:
            rephrased += " I request your prompt attention and appropriate action to resolve this matter."
        
        return rephrased

    # =================== HELPER METHODS ===================

    def _hash_roll_number(self, roll_number: str) -> str:
        """Create SHA-256 hash of roll number."""
        return hashlib.sha256(roll_number.encode()).hexdigest()

    def _default_sensitive_text(self, user_context: Dict[str, Any]) -> str:
        """Generate default text for sensitive content."""
        roll = (user_context.get('roll_number') or '').strip()
        who = f"Student {roll}" if roll else "The reporter"
        return (
            f"{who} requires immediate confidential assistance from the "
            "Student Council / Disciplinary Committee regarding a sensitive incident."
        )

    def _is_refusal_or_empty(self, text: str) -> bool:
        """Check if text is a refusal or too short."""
        t = (text or '').strip().lower()
        if len(t) < 10:
            return True
        
        refusal_phrases = [
            "cannot rephrase", "can't rephrase", "unable to rephrase",
            "cannot assist", "not allowed", "policy", "refuse to"
        ]
        
        return any(p in t for p in refusal_phrases)

    def _detect_department_from_text(self, txt: str) -> Optional[str]:
        """Detect department mention in text."""
        for alias, full in self.dept_alias.items():
            if re.search(rf'\b{re.escape(alias)}\b', txt, re.IGNORECASE):
                return full
            if re.search(rf'\b{re.escape(full.lower())}\b', txt):
                return full
        return None

    def _is_location_unclear(self, complaint: str) -> bool:
        """Check if location/ownership is unclear."""
        txt = complaint.lower()
        
        # No facility keywords = location is clear
        if not any(k in txt for k in self.context_facility_keywords):
            return False
        
        # Has clear ownership indicators = location is clear
        if any(h in txt for h in self.hostel_cues):
            return False
        if any(b in txt for b in self.building_keywords):
            return False
        if self._detect_department_from_text(txt):
            return False
        if any(k in txt for k in self.department_asset_keywords):
            return False
        
        # Facility mentioned but no clear owner = unclear
        return True

    def _preserve_reference_in_rephrase(
        self,
        original: str,
        rephrased: str,
        hints: Dict[str, Any]
    ) -> str:
        """Preserve department/block references in rephrased text."""
        if not rephrased:
            return rephrased
        
        mentioned_dept = hints.get('mentioned_department')
        if mentioned_dept:
            prefix = f"This complaint concerns facilities in {mentioned_dept}. "
            if not rephrased.lower().startswith(prefix.lower()):
                return prefix + rephrased
        
        return rephrased

    def _extract_routing_hints(
        self,
        complaint: str,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract routing hints from complaint."""
        txt = complaint.lower()
        mentioned_dept = self._detect_department_from_text(txt)
        
        return {
            'mentioned_department': mentioned_dept
        }

    def _determine_visibility_type(self, llm_visibility: str) -> str:
        """Convert LLM visibility to model visibility_type."""
        mapping = {
            'public': 'public',
            'private': 'private',
            'confidential': 'confidential'
        }
        
        return mapping.get(llm_visibility, 'public')

    # =================== ABUSIVE LANGUAGE DETECTION ===================
    
    def _detect_abusive_language(self, text: str) -> bool:
        """Detect abusive, profane, or very informal language."""
        txt = text.lower()
        
        # Common profanity patterns (partial words to catch variations)
        profanity_patterns = [
            'f***', 'f**k', 'sh**', 'b***h', 'a**', 'd**n', 'h**l',
            'damn', 'hell', 'crap', 'stupid', 'idiot', 'moron', 'fool'
        ]
        
        # Very informal/slang patterns
        informal_patterns = [
            'wtf', 'omg', 'lol', 'rofl', 'smh', 'tbh', 'ngl', 'fr',
            'bruh', 'dude', 'bro', 'yo', 'nah', 'yeah', 'yep', 'nope',
            'gonna', 'wanna', 'gotta', 'lemme', 'gimme', 'dunno'
        ]
        
        # Aggressive/violent language
        violent_patterns = [
            'kill', 'die', 'hate', 'destroy', 'attack', 'fight', 'beat',
            'punch', 'hit', 'hurt', 'harm', 'threat', 'violence'
        ]
        
        # Check for profanity
        for pattern in profanity_patterns:
            if pattern in txt:
                return True
        
        # Check for excessive informal language (3+ instances)
        informal_count = sum(1 for pattern in informal_patterns if pattern in txt)
        if informal_count >= 3:
            return True
        
        # Check for violent language in complaint context
        violent_count = sum(1 for pattern in violent_patterns if pattern in txt)
        if violent_count >= 2:
            return True
        
        # Check for excessive capitalization (shouting)
        if len([c for c in text if c.isupper()]) > len(text) * 0.5 and len(text) > 20:
            return True
        
        # Check for excessive punctuation (aggressive)
        if text.count('!') > 3 or text.count('?') > 5:
            return True
        
        return False
    
    def _formalize_text(self, text: str) -> str:
        """Convert informal/abusive text to formal language."""
        if not text:
            return text
        
        formalized = text
        
        # Replace common informal contractions
        replacements = {
            "gonna": "going to",
            "wanna": "want to",
            "gotta": "have to",
            "lemme": "let me",
            "gimme": "give me",
            "dunno": "do not know",
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "isn't": "is not",
            "doesn't": "does not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "wouldn't": "would not",
            "shouldn't": "should not",
            "couldn't": "could not",
            "mustn't": "must not",
            "ain't": "is not",
            "ya": "you",
            "yeah": "yes",
            "yep": "yes",
            "nope": "no",
            "nah": "no",
            "bruh": "sir/madam",
            "dude": "sir/madam",
            "bro": "sir/madam",
            "wtf": "what",
            "omg": "",
            "lol": "",
            "rofl": "",
            "smh": "",
            "tbh": "to be honest",
            "ngl": "to be honest",
            "fr": "for real"
        }
        
        # Apply replacements (case-insensitive)
        for informal, formal in replacements.items():
            pattern = re.compile(re.escape(informal), re.IGNORECASE)
            formalized = pattern.sub(formal, formalized)
        
        # Remove excessive punctuation
        formalized = re.sub(r'!{2,}', '.', formalized)  # Multiple ! to single .
        formalized = re.sub(r'\?{3,}', '?', formalized)  # Multiple ? to single ?
        
        # Remove excessive capitalization (convert to sentence case)
        words = formalized.split()
        if len([w for w in words if w.isupper() and len(w) > 1]) > len(words) * 0.3:
            formalized = formalized.capitalize()
        
        # Remove profanity (replace with [inappropriate language])
        profanity_words = ['damn', 'hell', 'crap', 'stupid', 'idiot', 'moron', 'fool']
        for word in profanity_words:
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            formalized = pattern.sub('[inappropriate language]', formalized)
        
        # Ensure proper sentence structure
        if not formalized.endswith(('.', '!', '?')):
            formalized += '.'
        
        return formalized.strip()
    
    def _flag_abusive_user(self, roll_number: str, complaint_id: str):
        """Flag user as abusive/violent speaker in Firebase."""
        try:
            from api.firebase_service import FirebaseService
            firebase_service = FirebaseService()
            
            roll_hash = self._hash_roll_number(roll_number)
            user_ref = firebase_service.db.collection('users').document(roll_hash)
            
            # Get or create user document
            user_doc = user_ref.get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                abusive_count = user_data.get('abusive_complaints_count', 0) + 1
                flagged_complaints = user_data.get('abusive_complaint_ids', [])
                flagged_complaints.append(complaint_id)
                
                user_ref.update({
                    'is_abusive_user': True,
                    'abusive_complaints_count': abusive_count,
                    'abusive_complaint_ids': flagged_complaints,
                    'last_abusive_complaint': complaint_id,
                    'last_flagged_at': datetime.now(timezone.utc).isoformat()
                })
            else:
                # Create new user document
                user_ref.set({
                    'roll_number_hash': roll_hash,
                    'is_abusive_user': True,
                    'abusive_complaints_count': 1,
                    'abusive_complaint_ids': [complaint_id],
                    'last_abusive_complaint': complaint_id,
                    'first_flagged_at': datetime.now(timezone.utc).isoformat(),
                    'last_flagged_at': datetime.now(timezone.utc).isoformat()
                })
            
            print(f"   ⚠️ User {roll_hash[:8]}... flagged as abusive/violent speaker")
        except Exception as e:
            print(f"   ⚠️ Failed to flag abusive user: {e}")
            # Don't fail the complaint processing if flagging fails
    
    def _create_fallback_complaint(
        self,
        submission: ComplaintSubmission,
        complaint_id: str,
        start_time: float,
        error_msg: str
    ) -> Complaint:
        """Create fallback complaint on processing error."""
        roll_hash = self._hash_roll_number(submission.roll_number)
        
        # Check for abusive language even in fallback
        contains_abusive = self._detect_abusive_language(submission.complaint_text)
        rephrased = self._formalize_text(submission.complaint_text) if contains_abusive else "Complaint processing encountered an error. Please review manually."
        
        complaint = Complaint(
            complaint_id=complaint_id,
            roll_number_hash=roll_hash,
            department=submission.department,
            gender=submission.gender,
            residence=submission.residence,
            original_text=submission.complaint_text,
            rephrased_text=rephrased,
            category='infrastructure',  # Default
            assigned_authority='Administrative Officer',  # Default
            routing_path=['Administrative Officer'],
            routing_reasoning=f'Fallback routing due to error: {error_msg}',
            hidden_from=[],
            bypass_applied=False,
            escalated_to=None,
            priority_level='Medium',
            priority_score=50.0,
            priority_breakdown=['Default priority due to processing error'],
            priority_emoji='🟡',
            status='raised',
            visibility_type='private',  # Default to private on error
            is_public=False,
            requires_image=False,
            image_requirement_reason='N/A',
            is_mandatory_image=False,
            image_urls=[],
            upvotes=0,
            downvotes=0,
            net_votes=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            opened_at=None,
            reviewed_at=None,
            closed_at=None,
            status_history=[],
            processing_time=time.time() - start_time,
            llm_model_used='error_fallback',
            llm_confidence='Low',
            contains_abusive_language=contains_abusive,
            language_issues="Informal or inappropriate language detected" if contains_abusive else None
        )
        
        # Flag user if abusive language detected
        if contains_abusive:
            self._flag_abusive_user(submission.roll_number, complaint_id)
        
        return complaint
