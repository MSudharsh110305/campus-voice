import json
from typing import Optional, Dict, Any, List
import requests
import re
from datetime import datetime
import time

class IntelligentLLMEngine:
    """Advanced LLM engine with visibility determination and professional rephrasing"""
    
    def __init__(self, config):
        self.config = config
        self.ollama_host = getattr(config, 'ollama_host', 'http://localhost:11434')
        self.ollama_timeout = getattr(config, 'ollama_timeout', 30)
        
        # Test Ollama availability
        self.ollama_available = self._test_ollama_connection()
        
        print(f"🧠 Intelligent LLM Engine initialized")
        print(f"   🔗 Ollama: {'✅ Available' if self.ollama_available else '❌ Using rule-based fallbacks'}")
        
        # Enhanced keyword sets for intelligent processing
        self._initialize_keyword_sets()
    
    def _initialize_keyword_sets(self):
        """Initialize comprehensive keyword sets for intelligent classification"""
        
        # Visibility determination keywords
        self.confidential_keywords = [
            'harassment', 'abuse', 'discrimination', 'inappropriate behavior',
            'sexual harassment', 'bullying', 'misconduct', 'assault', 'threat',
            'ragging', 'mental health', 'depression', 'anxiety', 'personal issue',
            'confidential', 'sensitive', 'private matter', 'don\'t tell anyone'
        ]
        
        self.private_keywords = [
            'personal', 'individual', 'specific to me', 'my issue', 'don\'t share',
            'between us', 'personally', 'individual case', 'just for me'
        ]
        
        # Category classification keywords
        self.category_keywords = {
            'hostel': [
                'hostel', 'mess', 'room', 'warden', 'deputy warden', 'food', 'wifi',
                'water', 'bathroom', 'cleanliness', 'laundry', 'electricity', 'fan',
                'ac', 'bed', 'dormitory', 'canteen', 'dining', 'hygiene', 'accommodation',
                'roommate', 'noise', 'security', 'entry', 'gate timing', 'curfew'
            ],
            'academic': [
                'professor', 'faculty', 'teacher', 'class', 'lecture', 'exam', 'test',
                'syllabus', 'curriculum', 'lab', 'laboratory', 'assignment', 'project',
                'marks', 'grades', 'teaching', 'subject', 'course', 'semester', 'practical',
                'theory', 'attendance', 'tutorial', 'evaluation', 'assessment', 'timetable',
                'schedule', 'internal', 'external', 'viva', 'presentation'
            ],
            'infrastructure': [
                'building', 'classroom', 'library', 'auditorium', 'lift', 'elevator',
                'parking', 'ground', 'playground', 'toilet', 'washroom', 'corridor',
                'staircase', 'roof', 'gate', 'security', 'maintenance', 'repair',
                'construction', 'facility', 'equipment', 'furniture', 'lighting',
                'ventilation', 'cleanliness', 'water supply', 'electricity supply'
            ]
        }
        
        # Building keywords for infrastructure classification
        self.building_keywords = [
            'library', 'main building', 'admin block', 'ece block', 'cse block',
            'it block', 'mechanical block', 'civil block', 'auditorium', 'seminar hall',
            'conference hall', 'workshop', 'canteen building', 'sports complex'
        ]
    
    def _test_ollama_connection(self) -> bool:
        """Test Ollama connection and available models"""
        try:
            resp = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get('models', [])
                if models:
                    print(f"   📋 Available models: {[m['name'] for m in models[:2]]}...")
                    return True
            return False
        except Exception as e:
            print(f"   ⚠️ Ollama test failed: {e}")
            return False
    
    def process_complaint_complete(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete LLM processing: rephrasing, visibility determination, and classification
        """
        
        print(f"🧠 Starting intelligent LLM processing...")
        start_time = time.time()
        
        try:
            if self.ollama_available:
                result = self._ollama_complete_processing(complaint, user_context)
            else:
                result = self._rule_based_complete_processing(complaint, user_context)
            
            result['processing_time'] = time.time() - start_time
            print(f"✅ LLM processing completed in {result['processing_time']:.2f}s")
            return result
            
        except Exception as e:
            print(f"❌ LLM processing failed: {e}")
            return self._fallback_processing(complaint, user_context, time.time() - start_time)
    
    def _ollama_complete_processing(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Complete processing using Ollama LLM"""
        
        system_prompt = """You are Campus Voice AI, an intelligent complaint processing system. 

Your task is to:
1. REPHRASE the complaint professionally and formally
2. DETERMINE appropriate visibility level
3. CLASSIFY the complaint category
4. PROVIDE reasoning

VISIBILITY LEVELS:
- public: General issues that can be shared with community for voting
- private: Personal issues that should remain confidential to administration
- confidential: Sensitive matters requiring highest discretion (harassment, abuse, etc.)

CATEGORIES:
- hostel: Dormitory, mess, accommodation, warden-related issues
- academic: Teaching, exams, curriculum, faculty-related issues  
- infrastructure: Buildings, facilities, equipment, maintenance issues

RULES:
- If mentions harassment, abuse, discrimination → confidential
- If very personal or individual-specific → private
- If general issue affecting multiple students → public
- If building names mentioned → infrastructure
- If teaching/faculty mentioned → academic
- If hostel/mess mentioned → hostel

Respond ONLY with valid JSON:
{
  "rephrased_complaint": "Professional version of the complaint",
  "visibility": "public/private/confidential",
  "category": "hostel/academic/infrastructure", 
  "confidence": "High/Medium/Low",
  "reasoning": "Brief explanation of decisions"
}"""

        prompt = f"""{system_prompt}

Original Complaint: {complaint}
User Department: {user_context.get('department', 'Unknown')}
User Residence: {user_context.get('residence', 'Unknown')}

Process this complaint:"""

        payload = {
            "model": "llama3:instruct",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
                "max_tokens": 500
            }
        }
        
        try:
            resp = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=self.ollama_timeout)
            
            if resp.status_code == 200:
                result = resp.json()
                response_text = result.get('response', '').strip()
                
                # Parse JSON response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        llm_result = json.loads(json_match.group())
                        
                        # Validate required fields
                        required_fields = ['rephrased_complaint', 'visibility', 'category']
                        if all(field in llm_result for field in required_fields):
                            
                            # Ensure valid values
                            if llm_result['visibility'] not in ['public', 'private', 'confidential']:
                                llm_result['visibility'] = 'public'
                            
                            if llm_result['category'] not in ['hostel', 'academic', 'infrastructure']:
                                llm_result['category'] = self._rule_based_classify_category(complaint)
                            
                            llm_result['model_used'] = 'llama3:instruct'
                            print(f"   🤖 Ollama processing successful")
                            print(f"   📝 Rephrased: {llm_result['rephrased_complaint'][:50]}...")
                            print(f"   🔓 Visibility: {llm_result['visibility']}")
                            print(f"   📂 Category: {llm_result['category']}")
                            
                            return llm_result
                    
                    except json.JSONDecodeError:
                        pass
                
                # If JSON parsing fails, extract information from text
                return self._parse_llm_text_response(response_text, complaint, user_context)
        
        except Exception as e:
            print(f"   ❌ Ollama request failed: {e}")
        
        # If Ollama fails, use rule-based processing
        raise Exception("Ollama processing failed")
    
    def _parse_llm_text_response(self, response_text: str, original_complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response when JSON extraction fails"""
        
        # Extract rephrased complaint (usually first paragraph)
        lines = response_text.split('\n')
        rephrased = ""
        for line in lines:
            line = line.strip()
            if line and not line.lower().startswith(('visibility:', 'category:', 'confidence:')):
                if len(line) > 20:  # Likely the rephrased complaint
                    rephrased = line
                    break
        
        if not rephrased:
            rephrased = self._rule_based_rephrase(original_complaint, user_context)
        
        # Extract visibility and category from text
        visibility = 'public'
        category = 'infrastructure'
        
        response_lower = response_text.lower()
        if 'confidential' in response_lower:
            visibility = 'confidential'
        elif 'private' in response_lower:
            visibility = 'private'
        
        if 'hostel' in response_lower:
            category = 'hostel'
        elif 'academic' in response_lower:
            category = 'academic'
        
        return {
            'rephrased_complaint': rephrased,
            'visibility': visibility,
            'category': category,
            'confidence': 'Medium',
            'reasoning': 'Parsed from LLM text response',
            'model_used': 'llama3:instruct'
        }
    
    def _rule_based_complete_processing(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Complete rule-based processing when Ollama is unavailable"""
        
        print(f"   🧠 Using intelligent rule-based processing...")
        
        # 1. Determine visibility
        visibility = self._determine_visibility_rules(complaint)
        
        # 2. Classify category  
        category = self._rule_based_classify_category(complaint)
        
        # 3. Rephrase complaint
        rephrased = self._rule_based_rephrase(complaint, user_context)
        
        print(f"   📝 Rule-based rephrasing applied")
        print(f"   🔓 Visibility: {visibility}")
        print(f"   📂 Category: {category}")
        
        return {
            'rephrased_complaint': rephrased,
            'visibility': visibility,
            'category': category,
            'confidence': 'High' if visibility == 'confidential' else 'Medium',
            'reasoning': f'Rule-based: {category} complaint, {visibility} visibility',
            'model_used': 'rule_based_engine'
        }
    
    def _determine_visibility_rules(self, complaint: str) -> str:
        """Intelligent rule-based visibility determination"""
        
        complaint_lower = complaint.lower()
        
        # Check for confidential keywords (highest priority)
        for keyword in self.confidential_keywords:
            if keyword in complaint_lower:
                return 'confidential'
        
        # Check for private keywords
        for keyword in self.private_keywords:
            if keyword in complaint_lower:
                return 'private'
        
        # Check for personal pronouns indicating individual issues
        personal_indicators = ['my ', 'i am', 'i have', 'i was', 'personally', 'individual']
        personal_count = sum(1 for indicator in personal_indicators if indicator in complaint_lower)
        
        if personal_count >= 2:
            return 'private'
        
        # Default to public for general issues
        return 'public'
    
    def _rule_based_classify_category(self, complaint: str) -> str:
        """Intelligent rule-based category classification"""
        
        complaint_lower = complaint.lower()
        
        # Check for building names (strong indicator for infrastructure)
        for building in self.building_keywords:
            if building.lower() in complaint_lower:
                return 'infrastructure'
        
        # Count keyword matches
        scores = {category: 0 for category in self.category_keywords}
        
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in complaint_lower:
                    scores[category] += 1
        
        # Apply bonus scoring for strong indicators
        if any(word in complaint_lower for word in ['warden', 'deputy warden']):
            scores['hostel'] += 5
        
        if any(word in complaint_lower for word in ['professor', 'faculty', 'teaching']):
            scores['academic'] += 5
        
        if any(word in complaint_lower for word in ['building', 'facility', 'maintenance']):
            scores['infrastructure'] += 3
        
        # Determine winner
        max_category = max(scores, key=scores.get)
        
        # If no clear winner, use smart defaults
        if scores[max_category] == 0:
            if any(word in complaint_lower for word in ['room', 'mess', 'food']):
                return 'hostel'
            elif any(word in complaint_lower for word in ['class', 'exam', 'study']):
                return 'academic'
            else:
                return 'infrastructure'
        
        return max_category
    
    def _rule_based_rephrase(self, complaint: str, user_context: Dict[str, Any]) -> str:
        """Professional rephrasing using intelligent rules"""
        
        rephrased = complaint.strip()
        
        # Add formal opening based on content
        if not rephrased.startswith(("I would like to", "We would like to", "This is to", "I am writing")):
            category = self._rule_based_classify_category(complaint)
            
            if category == 'hostel':
                rephrased = f"I would like to bring to your attention a hostel-related concern. {rephrased}"
            elif category == 'academic':
                rephrased = f"I am writing to address an academic matter that requires attention. {rephrased}"
            else:
                rephrased = f"This is to report an infrastructure issue that needs resolution. {rephrased}"
        
        # Apply formal language replacements
        formal_replacements = {
            " really ": " significantly ",
            " very ": " considerably ",
            " bad ": " inadequate ",
            " terrible ": " unsatisfactory ",
            " awesome ": " excellent ",
            " can't ": " cannot ",
            " won't ": " will not ",
            " don't ": " do not ",
            " isn't ": " is not ",
            " doesn't ": " does not ",
            " ain't ": " is not ",
            " gonna ": " going to ",
            " wanna ": " want to "
        }
        
        for casual, formal in formal_replacements.items():
            rephrased = rephrased.replace(casual, formal)
        
        # Ensure proper sentence structure
        if not rephrased.endswith('.'):
            rephrased += "."
        
        # Add professional closing for short complaints
        if len(rephrased) < 100:
            rephrased += " I request your prompt attention and appropriate action to resolve this matter."
        
        return rephrased
    
    def _fallback_processing(self, complaint: str, user_context: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Ultimate fallback processing that never fails"""
        
        return {
            'rephrased_complaint': complaint,  # Use original if rephrasing fails
            'visibility': 'public',  # Safe default
            'category': 'infrastructure',  # Safe default
            'confidence': 'Low',
            'reasoning': 'Fallback processing due to system errors',
            'model_used': 'fallback_system',
            'processing_time': processing_time
        }
