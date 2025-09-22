import time
from dataclasses import dataclass
from typing import Dict, Any, Optional

from config import Config
from llm_engine import OllamaClient
from authority_mapper import AuthorityMapper
from priority_scorer import PriorityScorer

@dataclass
class ClassificationResult:
    category: str
    final_authority: str
    routing_path: list
    priority_level: str
    confidence: str
    reasoning: str
    bypass_applied: bool
    processing_time: float
    model_used: str
    used_image: bool
    upvotes: int
    detailed_analysis: Dict[str, Any]

class CampusVoiceClassifier:
    """Main classifier for Campus Voice complaints"""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.llm_client = OllamaClient(self.config)
        self.authority_mapper = AuthorityMapper(self.config)
        self.priority_scorer = PriorityScorer(self.config)

    def _llm_category_with_rules(self, complaint: str, user_department: str,
                                 image_data: Optional[str], user_residence: Optional[str]) -> Dict[str, Any]:
        # LLM primary classification
        cls = self.llm_client.classify_complaint(complaint, image_data)

        text_l = complaint.lower()

        # Hard rule: building name → infrastructure
        if any(b in text_l for b in self.config.building_names):
            cls["category"] = "infrastructure"
            cls["reasoning"] += " | Building name detected → infrastructure"

        # Subtle cross-facilities rule:
        # If hosteller and mentions facilities (bathroom/drinking water) with no building, prefer hostel
        if user_residence and user_residence.lower().startswith("hostel"):
            if any(f in text_l for f in self.config.cross_facilities) and not any(b in text_l for b in self.config.building_names):
                cls["category"] = "hostel"
                cls["reasoning"] += " | Hosteller with facility complaint (no building) → hostel"

        # Academic disambiguation for teaching complaints
        if any(k in text_l for k in ["teach", "teaching", "explain", "concept", "class", "lecture", "syllabus", "lab", "faculty", "professor", "mam", "sir"]):
            # If it smells like teaching/staff, ensure academic
            cls["category"] = "academic"
            cls["reasoning"] += " | Teaching/staff keywords → academic"

        return cls

    def classify(self, complaint: str, user_department: str, upvotes: int = 0,
                 image_data: Optional[str] = None, user_residence: Optional[str] = None) -> ClassificationResult:
        start_time = time.time()

        # Get category with hybrid logic
        classification = self._llm_category_with_rules(
            complaint=complaint,
            user_department=user_department,
            image_data=image_data,
            user_residence=user_residence
        )
        category = classification['category']

        # Determine hostel bypass if relevant
        bypass_info = self.llm_client.detect_authority_bypass(complaint, category, image_data)

        # Route to correct authority
        routing = self.authority_mapper.route_complaint(
            category=category,
            user_department=user_department,
            needs_bypass=bypass_info['needs_bypass'],
            mentioned_authority=bypass_info['mentioned_authority']
        )

        # Priority scoring (support signal only)
        priority = self.priority_scorer.calculate_priority(complaint, upvotes)

        reasoning_parts = [
            classification['reasoning'],
            routing['reasoning'],
            priority['reasoning']
        ]
        if bypass_info['needs_bypass']:
            reasoning_parts.append(f"Authority bypass: {bypass_info['reasoning']}")
        full_reasoning = " | ".join(reasoning_parts)

        processing_time = time.time() - start_time

        return ClassificationResult(
            category=category,
            final_authority=routing['final_authority'],
            routing_path=routing['routing_path'],
            priority_level=priority['level'],
            confidence=classification.get('confidence', 'Medium'),
            reasoning=full_reasoning,
            bypass_applied=routing['bypass_applied'],
            processing_time=processing_time,
            model_used=self.config.current_model or "llm",
            used_image=image_data is not None,
            upvotes=upvotes,
            detailed_analysis={
                'classification': classification,
                'bypass_info': bypass_info,
                'routing': routing,
                'priority': priority
            }
        )
