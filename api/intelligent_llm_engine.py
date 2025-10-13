import json
from typing import Optional, Dict, Any, List
import requests
import re
import time

class IntelligentLLMEngine:
    """Advanced LLM engine with visibility determination and professional rephrasing (text-only)"""

    def __init__(self, config):
        self.config = config
        self.ollama_host = getattr(config, 'ollama_host', 'http://localhost:11434')
        self.ollama_timeout = getattr(config, 'ollama_timeout', 30)

        # Test Ollama availability
        self.ollama_available = self._test_ollama_connection()

        print("🧠 Intelligent LLM Engine initialized")
        print(f"   🔗 Ollama: {'✅ Available' if self.ollama_available else '❌ Using rule-based fallbacks'}")

        # Enhanced keyword sets for intelligent processing
        self._initialize_keyword_sets()

    def _initialize_keyword_sets(self):
        """Initialize comprehensive keyword sets for intelligent classification and routing hints"""

        # Visibility determination keywords
        self.confidential_keywords = [
            'harassment', 'abuse', 'discrimination', 'inappropriate behavior',
            'sexual harassment', 'bullying', 'misconduct', 'assault', 'threat',
            'ragging', 'mental health', 'depression', 'anxiety', 'personal issue',
            'confidential', 'sensitive', 'private matter', "don't tell anyone"
        ]

        self.private_keywords = [
            'personal', 'individual', 'specific to me', 'my issue', "don't share",
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

        # Department aliases for detection in free text
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
            "management": "Management Studies",
        }

    def _test_ollama_connection(self) -> bool:
        """Test Ollama connection and available models"""
        try:
            resp = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = resp.json().get('models', [])
                if models:
                    print(f"   📋 Available models: {[m.get('name') for m in models[:2]]}...")
                return True
            return False
        except Exception as e:
            print(f"   ⚠️ Ollama test failed: {e}")
            return False

    def process_complaint_complete(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete LLM processing: rephrasing, visibility determination, and classification
        Also emits:
        - mentioned_department: if a different department is referenced
        - needs_bypass + mentioned_authority: if hostel authority is targeted
        """
        print("🧠 Starting intelligent LLM processing...")
        start_time = time.time()

        try:
            if self.ollama_available:
                result = self._ollama_complete_processing(complaint, user_context)
            else:
                result = self._rule_based_complete_processing(complaint, user_context)

            # Post-process to add hints for routing
            hints = self._extract_routing_hints(complaint, user_context)
            result.update(hints)

            result['processing_time'] = time.time() - start_time
            print(f"✅ LLM processing completed in {result['processing_time']:.2f}s")
            return result

        except Exception as e:
            print(f"❌ LLM processing failed: {e}")
            rb = self._rule_based_complete_processing(complaint, user_context)
            rb.update(self._extract_routing_hints(complaint, user_context))
            rb['processing_time'] = time.time() - start_time
            return rb

    # ------------------------ Ollama path ------------------------

    def _ollama_complete_processing(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Complete processing using Ollama LLM"""
        system_prompt = """You are Campus Voice AI, an intelligent complaint processing system.

Use the provided user context to rephrase and judge visibility appropriately. 
When rephrasing, maintain a professional tone and avoid gendered wording unless relevant.

User context schema:
- user_id: identifier for accountability
- gender: male/female/other
- department: complainant's department
- residence: hostel name or 'Day Scholar'

Tasks:
1) REPHRASE the complaint professionally (use gender/residence/department only if relevant)
2) DETERMINE visibility: public/private/confidential (see rules)
3) CLASSIFY category: hostel/academic/infrastructure (see rules)
4) PROVIDE reasoning

Rules:
- Mention of harassment/abuse/discrimination → confidential
- Highly personal individual case → private
- General issues affecting many → public
- Buildings/facilities → infrastructure
- Teaching/faculty/labs/equipment within a department → academic
- Hostel/mess, warden chain → hostel

Output ONLY valid JSON:
{
  "rephrased_complaint": "...",
  "visibility": "public|private|confidential",
  "category": "hostel|academic|infrastructure",
  "confidence": "High|Medium|Low",
  "reasoning": "..."
}"""

        prompt = f"""{system_prompt}

Original Complaint: {complaint}
User Context:
- user_id: {user_context.get('user_id', 'unknown')}
- gender: {user_context.get('gender', 'unknown')}
- department: {user_context.get('department', 'unknown')}
- residence: {user_context.get('residence', 'unknown')}

Process this complaint:"""

        payload = {
            "model": "llama3:instruct",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9, "max_tokens": 500}
        }

        resp = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=self.ollama_timeout)
        resp.raise_for_status()
        response_text = (resp.json().get('response') or "").strip()

        # Try strict JSON extraction
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                llm_result = json.loads(json_match.group())
                # Validate and normalize
                if llm_result.get('visibility') not in ['public', 'private', 'confidential']:
                    llm_result['visibility'] = 'public'
                if llm_result.get('category') not in ['hostel', 'academic', 'infrastructure']:
                    llm_result['category'] = self._rule_based_classify_category(complaint)
                llm_result['model_used'] = 'llama3:instruct'
                print("   🤖 Ollama processing successful")
                return llm_result
            except json.JSONDecodeError:
                pass

        # Fallback: parse from text
        return self._parse_llm_text_response(response_text, complaint, user_context)

    # ------------------------ Parsing and Rule-based ------------------------

    def _parse_llm_text_response(self, response_text: str, original_complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response when JSON extraction fails"""
        lines = response_text.split('\n')
        rephrased = ""
        for line in lines:
            line = line.strip()
            if line and not line.lower().startswith(('visibility:', 'category:', 'confidence:')):
                if len(line) > 20:
                    rephrased = line
                    break

        if not rephrased:
            rephrased = self._rule_based_rephrase(original_complaint, user_context)

        visibility = 'public'
        category = 'infrastructure'
        rl = response_text.lower()
        if 'confidential' in rl:
            visibility = 'confidential'
        elif 'private' in rl:
            visibility = 'private'
        if 'hostel' in rl:
            category = 'hostel'
        elif 'academic' in rl or 'professor' in rl or 'lab' in rl:
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
        print("   🧠 Using intelligent rule-based processing...")
        visibility = self._determine_visibility_rules(complaint)
        category = self._rule_based_classify_category(complaint)
        rephrased = self._rule_based_rephrase(complaint, user_context)
        print("   📝 Rule-based rephrasing applied")
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
        txt = complaint.lower()
        for kw in self.confidential_keywords:
            if kw in txt:
                return 'confidential'
        for kw in self.private_keywords:
            if kw in txt:
                return 'private'
        indicators = ['my ', 'i am', 'i have', 'i was', 'personally', 'individual']
        if sum(1 for i in indicators if i in txt) >= 2:
            return 'private'
        return 'public'

    def _rule_based_classify_category(self, complaint: str) -> str:
        """Intelligent rule-based category classification"""
        txt = complaint.lower()
        for b in self.building_keywords:
            if b.lower() in txt:
                return 'infrastructure'
        scores = {k: 0 for k in self.category_keywords}
        for cat, kws in self.category_keywords.items():
            for kw in kws:
                if kw.lower() in txt:
                    scores[cat] += 1
        if any(w in txt for w in ['warden', 'deputy warden']):
            scores['hostel'] += 5
        if any(w in txt for w in ['professor', 'faculty', 'teaching', 'lab', 'laboratory']):
            scores['academic'] += 5
        if any(w in txt for w in ['building', 'facility', 'maintenance']):
            scores['infrastructure'] += 3
        max_cat = max(scores, key=scores.get)
        if scores[max_cat] == 0:
            if any(w in txt for w in ['room', 'mess', 'food']):
                return 'hostel'
            if any(w in txt for w in ['class', 'exam', 'study']):
                return 'academic'
            return 'infrastructure'
        return max_cat

    def _rule_based_rephrase(self, complaint: str, user_context: Dict[str, Any]) -> str:
        """Professional rephrasing with context-aware opening"""
        rephrased = complaint.strip()
        if not rephrased.startswith(("I would like to", "We would like to", "This is to", "I am writing")):
            cat = self._rule_based_classify_category(complaint)
            if cat == 'hostel':
                rephrased = f"I would like to bring to your attention a hostel-related concern. {rephrased}"
            elif cat == 'academic':
                rephrased = f"I am writing to address an academic matter that requires attention. {rephrased}"
            else:
                rephrased = f"This is to report an infrastructure issue that needs resolution. {rephrased}"

        replacements = {
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
        for k, v in replacements.items():
            rephrased = rephrased.replace(k, v)
        if not rephrased.endswith('.'):
            rephrased += "."
        if len(rephrased) < 100:
            rephrased += " I request your prompt attention and appropriate action to resolve this matter."
        return rephrased

    # ------------------------ Routing hints ------------------------

    def _extract_routing_hints(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derive:
        - mentioned_department: department referenced in the text (may differ from user's department)
        - needs_bypass + mentioned_authority: if the complaint targets hostel authorities
        """
        txt = complaint.lower()
        mentioned_dept = None

        # Detect explicit department mentions via aliases or full names
        for alias, full in self.dept_alias.items():
            if re.search(rf'\b{re.escape(alias)}\b', txt) or re.search(rf'\b{re.escape(full.lower())}\b', txt):
                mentioned_dept = full
                break

        needs_bypass = False
        mentioned_authority = "none"
        # Heuristics for authority targeting
        if 'warden' in txt:
            # If specifically says "warden", bypass warden to deputy
            needs_bypass = True
            mentioned_authority = "warden"
        if 'deputy warden' in txt:
            # If targets deputy warden, bypass both to senior deputy warden
            needs_bypass = True
            mentioned_authority = "deputy_warden"

        return {
            'mentioned_department': mentioned_dept,
            'needs_bypass': needs_bypass,
            'mentioned_authority': mentioned_authority
        }
