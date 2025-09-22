from typing import Dict, Any
from config import Config

class PriorityScorer:
    """Calculate priority based on complaint content and upvotes"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def calculate_priority(self, complaint: str, upvotes: int) -> Dict[str, Any]:
        """Calculate priority score based on content analysis and upvotes"""
        
        complaint_lower = complaint.lower()
        score = 0.0
        factors = {}
        
        # Factor 1: Sensitive content (50% weight) - highest priority
        sensitive_count = sum(1 for keyword in self.config.sensitive_keywords 
                            if keyword in complaint_lower)
        sensitive_score = min(1.0, sensitive_count * 1.0)
        score += sensitive_score * 0.5
        factors['sensitive'] = {'count': sensitive_count, 'score': sensitive_score}
        
        # Factor 2: Urgency keywords (25% weight)
        urgency_count = sum(1 for keyword in self.config.urgency_keywords 
                          if keyword in complaint_lower)
        urgency_score = min(1.0, urgency_count * 0.5)
        score += urgency_score * 0.25
        factors['urgency'] = {'count': urgency_count, 'score': urgency_score}
        
        # Factor 3: Safety keywords (15% weight)
        safety_count = sum(1 for keyword in self.config.safety_keywords 
                         if keyword in complaint_lower)
        safety_score = min(1.0, safety_count * 0.6)
        score += safety_score * 0.15
        factors['safety'] = {'count': safety_count, 'score': safety_score}
        
        # Factor 4: Community upvotes (10% weight)
        upvote_score = min(1.0, upvotes / 20)  # 20 upvotes = max score
        score += upvote_score * 0.1
        factors['upvotes'] = {'count': upvotes, 'score': upvote_score}
        
        # Determine priority level
        if sensitive_count > 0:
            level = 'critical'  # Any sensitive content is critical
        elif score >= 0.7:
            level = 'critical'
        elif score >= 0.5:
            level = 'high'
        elif score >= 0.3:
            level = 'medium'
        else:
            level = 'low'
        
        # Generate reasoning
        reasoning_parts = []
        if sensitive_count > 0:
            reasoning_parts.append(f"{sensitive_count} sensitive content indicators")
        if urgency_count > 0:
            reasoning_parts.append(f"{urgency_count} urgency keywords")
        if safety_count > 0:
            reasoning_parts.append(f"{safety_count} safety concerns")
        if upvotes > 0:
            reasoning_parts.append(f"{upvotes} community upvotes")
        
        reasoning = f"Priority factors: {', '.join(reasoning_parts) if reasoning_parts else 'standard complaint'}"
        
        return {
            'level': level,
            'score': score,
            'factors': factors,
            'reasoning': reasoning
        }
