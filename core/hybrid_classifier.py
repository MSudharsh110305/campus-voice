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
    
    def classify(self, complaint: str, user_department: str, upvotes: int = 0, 
                image_data: Optional[str] = None) -> ClassificationResult:
        """Main classification method"""
        
        start_time = time.time()
        
        # Step 1: Classify into main category (hostel/academic/infrastructure)
        classification = self.llm_client.classify_complaint(complaint, image_data)
        category = classification['category']
        
        # Step 2: Check for authority bypass (only for hostel complaints)
        bypass_info = self.llm_client.detect_authority_bypass(complaint, category, image_data)
        
        # Step 3: Route to correct authority
        routing = self.authority_mapper.route_complaint(
            category=category,
            user_department=user_department,
            needs_bypass=bypass_info['needs_bypass'],
            mentioned_authority=bypass_info['mentioned_authority']
        )
        
        # Step 4: Calculate priority
        priority = self.priority_scorer.calculate_priority(complaint, upvotes)
        
        # Step 5: Generate overall reasoning
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
            confidence=classification['confidence'],
            reasoning=full_reasoning,
            bypass_applied=routing['bypass_applied'],
            processing_time=processing_time,
            model_used=self.config.current_model or "keyword-based",
            used_image=image_data is not None,
            upvotes=upvotes,
            detailed_analysis={
                'classification': classification,
                'bypass_info': bypass_info,
                'routing': routing,
                'priority': priority
            }
        )
