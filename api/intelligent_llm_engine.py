import json
from typing import Optional, Dict, Any
import requests
import re
import time

class IntelligentLLMEngine:
    """Advanced LLM engine with visibility determination and professional rephrasing (text-only)"""

    def __init__(self, config):
        self.config = config
        self.ollama_host = getattr(config, 'ollama_host', 'http://localhost:11434')
        self.ollama_timeout = getattr(config, 'ollama_timeout', 30)
        # Make model configurable; default to gemma3:latest
        self.ollama_model = getattr(config, 'ollama_model', 'gemma3:latest')

        # Test Ollama availability
        self.ollama_available = self._test_ollama_connection()

        print("🧠 Intelligent LLM Engine initialized")
        print(f"   🔗 Ollama: {'✅ Available' if self.ollama_available else '❌ Using rule-based fallbacks'}")
        print(f"   🧠 Default model: {self.ollama_model}")

        # Enhanced keyword sets for intelligent processing
        self._initialize_keyword_sets()

    def _initialize_keyword_sets(self):
        """Initialize comprehensive keyword sets for intelligent classification and routing hints"""

        self.confidential_keywords = [
            'harassment', 'harassed', 'harass', 'sexual harassment', 'sexual',
            'abuse', 'abused', 'assault', 'molest', 'molestation',
            'discrimination', 'ragging', 'threat', 'stalking',
            'inappropriate behavior', 'misconduct',
            'mental health', 'depression', 'anxiety',
            'confidential', 'sensitive', "private matter", "don't tell anyone"
        ]

        self.private_keywords = [
            'personal', 'individual', 'specific to me', 'my issue', "don't share",
            'between us', 'personally', 'individual case', 'just for me'
        ]

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
                'schedule', 'internal', 'external', 'viva', 'presentation', 'classmate', 'peer', 'student'
            ],
            'infrastructure': [
                'building', 'classroom', 'library', 'auditorium', 'lift', 'elevator',
                'parking', 'ground', 'playground', 'toilet', 'washroom', 'corridor',
                'staircase', 'roof', 'gate', 'security', 'maintenance', 'repair',
                'construction', 'facility', 'equipment', 'furniture', 'lighting',
                'ventilation', 'cleanliness', 'water supply', 'electricity supply', 'plumbing'
            ]
        }

        self.building_keywords = [
            'block a', 'block b', 'block c', 'main building', 'admin block',
            'ece block', 'cse block', 'it block', 'mechanical block', 'civil block',
            'library', 'auditorium', 'seminar hall', 'conference hall', 'workshop',
            'canteen building', 'sports complex'
        ]

        self.context_facility_keywords = [
            'drinking water', 'water', 'bathroom', 'toilet', 'electricity', 'power', 'plumbing'
        ]

        self.department_asset_keywords = [
            '3d printer', 'oscilloscope', 'cnc', 'lathe', 'soldering', 'department lab', 'dept lab', 'project lab',
            'instrument', 'instruments', 'equipment', 'laboratory', 'lab'
        ]

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

        self.block_to_dept = {
            'mechanical block': 'Mechanical Engineering',
            'ece block': 'Electronics & Communication Engineering',
            'cse block': 'Computer Science & Engineering',
            'it block': 'Information Technology',
            'civil block': 'Civil Engineering'
        }

        self.hostel_cues = ['hostel', 'warden', 'deputy warden', 'mess', 'curfew', 'room ']

    def _test_ollama_connection(self) -> bool:
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
        print("🧠 Starting intelligent LLM processing...")
        start_time = time.time()

        try:
            if self.ollama_available:
                print(f"   🧠 Model in use: {self.ollama_model}")
                result = self._ollama_complete_processing(complaint, user_context)
            else:
                result = self._rule_based_complete_processing(complaint, user_context)

            # Routing hints
            hints = self._extract_routing_hints(complaint, user_context)
            result.update(hints)

            # Preserve referenced department/block in rephrase when present
            result['rephrased_complaint'] = self._preserve_reference_in_rephrase(
                original=complaint, rephrased=result.get('rephrased_complaint', ''), hints=hints
            )

            # Category override for context + sensitive
            result['category'] = self._context_aware_category(
                complaint, user_context, preferred=result.get('category')
            )

            # Sensitive handling
            if self._has_confidential_content(complaint):
                result['visibility'] = 'confidential'
                if self._is_refusal_or_empty(result.get('rephrased_complaint', '')):
                    result['rephrased_complaint'] = self._default_sensitive_text(user_context)

            # Insufficient info detection
            if self._is_location_unclear(complaint):
                result['needs_clarification'] = True
                result['visibility'] = 'private'
                result['category'] = 'infrastructure'
                result['confidence'] = 'Low'
                result['rephrased_complaint'] = (
                    "Please include the exact location/ownership (Hostel name/room, Block/Classroom, or Department/Lab/Equipment) "
                    "so this can be routed correctly."
                )

            result['processing_time'] = time.time() - start_time
            print(f"✅ LLM processing completed in {result['processing_time']:.2f}s")
            return result

        except Exception as e:
            print(f"❌ LLM processing failed: {e}")
            rb = self._rule_based_complete_processing(complaint, user_context)
            rb.update(self._extract_routing_hints(complaint, user_context))
            rb['rephrased_complaint'] = self._preserve_reference_in_rephrase(
                original=complaint, rephrased=rb.get('rephrased_complaint', ''), hints=rb
            )
            rb['category'] = self._context_aware_category(complaint, user_context, preferred=rb.get('category'))
            if self._has_confidential_content(complaint):
                rb['visibility'] = 'confidential'
                if self._is_refusal_or_empty(rb.get('rephrased_complaint', '')):
                    rb['rephrased_complaint'] = self._default_sensitive_text(user_context)
            if self._is_location_unclear(complaint):
                rb['needs_clarification'] = True
                rb['visibility'] = 'private'
                rb['category'] = 'infrastructure'
                rb['confidence'] = 'Low'
                rb['rephrased_complaint'] = (
                    "Please include the exact location/ownership (Hostel name/room, Block/Classroom, or Department/Lab/Equipment) "
                    "so this can be routed correctly."
                )
            rb['processing_time'] = time.time() - start_time
            return rb

    def _ollama_complete_processing(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = """You are Campus Voice AI, an intelligent complaint processing system.

Use the provided user context to rephrase and judge visibility appropriately.
When rephrasing, maintain a professional tone and avoid gendered wording unless relevant.
Never refuse to rephrase sensitive content; if it’s sensitive, write a neutral one-line summary suitable for confidential handling.

User context schema:
- user_id: identifier for accountability
- gender: male/female/other
- department: complainant's department
- residence: hostel name or 'Day Scholar'

Tasks:
1) REPHRASE the complaint professionally (one to two sentences; never refuse)
2) DETERMINE visibility: public/private/confidential (see rules)
3) CLASSIFY category: hostel/academic/infrastructure (see rules)
4) PROVIDE reasoning (brief and specific)

Rules:
- Mention of harassment/abuse/sexual misconduct/discrimination → visibility must be 'confidential'
- Highly personal individual case → 'private'
- General issues affecting many → 'public'
- Buildings/blocks/facilities explicitly named → 'infrastructure'
- Hostel basic facilities (water, bathroom, electricity, plumbing) where the text mentions hostel cues → 'hostel'
- Teaching/faculty/labs/equipment within a department → 'academic'
- Classroom is always a facility-level issue (infrastructure)

Respond ONLY with valid JSON:
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
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.15, "top_p": 0.9, "max_tokens": 480}
        }

        resp = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=self.ollama_timeout)
        resp.raise_for_status()
        response_text = (resp.json().get('response') or "").strip()

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                llm_result = json.loads(json_match.group())
                if llm_result.get('visibility') not in ['public', 'private', 'confidential']:
                    llm_result['visibility'] = 'public'
                if llm_result.get('category') not in ['hostel', 'academic', 'infrastructure']:
                    llm_result['category'] = self._rule_based_classify_category(complaint)
                if self._has_confidential_content(complaint):
                    llm_result['visibility'] = 'confidential'
                    if self._is_refusal_or_empty(llm_result.get('rephrased_complaint', '')):
                        llm_result['rephrased_complaint'] = self._default_sensitive_text(user_context)

                llm_result['model_used'] = self.ollama_model
                print(f"   🤖 Ollama processing successful with model: {self.ollama_model}")
                return llm_result
            except json.JSONDecodeError:
                pass

        parsed = self._parse_llm_text_response(response_text, complaint, user_context)
        if self._has_confidential_content(complaint):
            parsed['visibility'] = 'confidential'
            if self._is_refusal_or_empty(parsed.get('rephrased_complaint', '')):
                parsed['rephrased_complaint'] = self._default_sensitive_text(user_context)
        parsed['model_used'] = self.ollama_model
        return parsed

    def _parse_llm_text_response(self, response_text: str, original_complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
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
        category = self._rule_based_classify_category(original_complaint)
        rl = response_text.lower()
        if 'confidential' in rl:
            visibility = 'confidential'
        elif 'private' in rl:
            visibility = 'private'
        if 'hostel' in rl:
            category = 'hostel'
        elif any(k in rl for k in ['academic', 'professor', 'lab', 'class']):
            category = 'academic'

        return {
            'rephrased_complaint': rephrased,
            'visibility': visibility,
            'category': category,
            'confidence': 'Medium',
            'reasoning': 'Parsed from LLM text response',
            'model_used': self.ollama_model
        }

    def _rule_based_complete_processing(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        print("   🧠 Using intelligent rule-based processing...")
        visibility = self._determine_visibility_rules(complaint)
        category = self._context_aware_category(complaint, user_context, preferred=self._rule_based_classify_category(complaint))
        rephrased = self._rule_based_rephrase(complaint, user_context)
        if self._has_confidential_content(complaint):
            visibility = 'confidential'
            if self._is_refusal_or_empty(rephrased):
                rephrased = self._default_sensitive_text(user_context)

        print(f"   🔧 Rule-based engine category: {category}")
        return {
            'rephrased_complaint': rephrased,
            'visibility': visibility,
            'category': category,
            'confidence': 'High' if visibility == 'confidential' else 'Medium',
            'reasoning': f'Rule-based: {category} complaint, {visibility} visibility',
            'model_used': 'rule_based_engine'
        }

    def _determine_visibility_rules(self, complaint: str) -> str:
        txt = complaint.lower()
        if self._has_confidential_content(txt):
            return 'confidential'
        for kw in self.private_keywords:
            if kw in txt:
                return 'private'
        indicators = ['my ', 'i am', 'i have', 'i was', 'personally', 'individual']
        if sum(1 for i in indicators if i in txt) >= 2:
            return 'private'
        return 'public'

    def _has_confidential_content(self, complaint: str) -> bool:
        txt = complaint.lower()
        return any(kw in txt for kw in self.confidential_keywords)

    def _rule_based_classify_category(self, complaint: str) -> str:
        txt = complaint.lower()
        for b in self.building_keywords:
            if b in txt:
                return 'infrastructure'
        scores = {k: 0 for k in self.category_keywords}
        for cat, kws in self.category_keywords.items():
            for kw in kws:
                if kw in txt:
                    scores[cat] += 1
        if any(w in txt for w in ['warden', 'deputy warden']):
            scores['hostel'] += 5
        if any(w in txt for w in ['professor', 'faculty', 'teaching', 'lab', 'laboratory', 'classmate', 'peer', 'student']):
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

    def _context_aware_category(self, complaint: str, user_context: Dict[str, Any], preferred: Optional[str]) -> str:
        """
        Context rules:
        - Department asset (lab/equipment) → academic, even if a block is named
        - Classroom is always infrastructure (AO)
        - Explicit building/block (without asset) → infrastructure (AO)
        - Facilities (water/bathroom/electricity/plumbing):
            - Only 'hostel' when text includes hostel cues; residence alone is not sufficient
            - Otherwise infrastructure (AO)
        - Sensitive content → academic (disciplinary)
        """
        txt = complaint.lower()
        residence = (user_context.get('residence') or '').lower()

        if self._has_confidential_content(txt):
            return 'academic'

        if 'classroom' in txt or 'class room' in txt:
            return 'infrastructure'

        if any(k in txt for k in self.department_asset_keywords):
            target = self._detect_department_from_text(txt) or self._infer_department_from_block(txt)
            if target:
                return 'academic'

        if any(b in txt for b in self.building_keywords):
            return 'infrastructure'

        if any(k in txt for k in self.context_facility_keywords):
            if any(h in txt for h in self.hostel_cues):
                return 'hostel'
            return 'infrastructure'

        return preferred or self._rule_based_classify_category(complaint)

    def _default_sensitive_text(self, user_context: Dict[str, Any]) -> str:
        uid = (user_context.get('user_id') or '').strip()
        who = f"The user {uid}" if uid else "The reporter"
        return f"{who} needs immediate confidential assistance from the Student Council / Disciplinary Committee regarding a sensitive incident."

    def _is_refusal_or_empty(self, text: str) -> bool:
        t = (text or '').strip().lower()
        if len(t) < 10:
            return True
        refusal_phrases = [
            "cannot rephrase", "can't rephrase", "won't rephrase", "unable to rephrase",
            "cannot assist", "can't assist", "not allowed", "policy", "refuse to", "i cannot"
        ]
        return any(p in t for p in refusal_phrases)

    def _detect_department_from_text(self, txt: str) -> Optional[str]:
        for alias, full in self.dept_alias.items():
            if re.search(rf'\b{re.escape(alias)}\b', txt) or re.search(rf'\b{re.escape(full.lower())}\b', txt):
                return full
        return None

    def _infer_department_from_block(self, txt: str) -> Optional[str]:
        for block_phrase, dept in self.block_to_dept.items():
            if block_phrase in txt:
                return dept
        return None

    def _is_location_unclear(self, complaint: str) -> bool:
        """
        True if facilities keywords are present but there is no clear owner:
        - no hostel cues, no building/block, no department mention, and no asset/lab terms
        """
        txt = complaint.lower()
        if not any(k in txt for k in self.context_facility_keywords):
            return False
        if any(h in txt for h in self.hostel_cues):
            return False
        if any(b in txt for b in self.building_keywords):
            return False
        if self._detect_department_from_text(txt):
            return False
        if any(k in txt for k in self.department_asset_keywords):
            return False
        return True

    def _preserve_reference_in_rephrase(self, original: str, rephrased: str, hints: Dict[str, Any]) -> str:
        """
        Ensure the rephrased text keeps the referenced department or block if present,
        avoiding substitution with the user's department.
        """
        if not rephrased:
            return rephrased
        txt = original.lower()
        mentioned_dept = hints.get('mentioned_department')
        block_hit = None
        for b in self.building_keywords:
            if b in txt:
                block_hit = b
                break
        prefix = ""
        if mentioned_dept:
            prefix = f"This complaint concerns the facilities in {mentioned_dept}. "
        elif block_hit:
            prefix = f"This complaint concerns the facilities in {block_hit}. "
        if prefix and not rephrased.lower().startswith(prefix.lower()):
            return prefix + rephrased
        return rephrased

    def _rule_based_rephrase(self, complaint: str, user_context: Dict[str, Any]) -> str:
        if self._has_confidential_content(complaint):
            return self._default_sensitive_text(user_context)

        rephrased = complaint.strip()
        if not rephrased.startswith(("I would like to", "We would like to", "This is to", "I am writing", "I am reporting")):
            cat = self._context_aware_category(complaint, user_context, preferred=self._rule_based_classify_category(complaint))
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

    def _extract_routing_hints(self, complaint: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        txt = complaint.lower()
        mentioned_dept = self._detect_department_from_text(txt)
        needs_bypass = False
        mentioned_authority = "none"
        if 'deputy warden' in txt:
            needs_bypass = True
            mentioned_authority = "deputy_warden"
        elif 'warden' in txt:
            needs_bypass = True
            mentioned_authority = "warden"
        return {
            'mentioned_department': mentioned_dept,
            'needs_bypass': needs_bypass,
            'mentioned_authority': mentioned_authority
        }
