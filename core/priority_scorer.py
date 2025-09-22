from typing import Dict
from config import Config

class PriorityScorer:
    def __init__(self, config: Config):
        self.cfg = config

    def calculate_priority(self, complaint: str, upvotes: int = 0) -> Dict[str, str]:
        text = complaint.lower()
        score = 0
        # urgency
        if any(k in text for k in self.cfg.urgency_keywords):
            score += 2
        # safety
        if any(k in text for k in self.cfg.safety_keywords):
            score += 3
        # crowd impact
        score += min(max(upvotes, 0) // 10, 3)

        if score >= 5:
            level = "High"
        elif score >= 2:
            level = "Medium"
        else:
            level = "Low"

        return {
            "level": level,
            "reasoning": f"Urgency/Safety/Upvotes composite score={score}"
        }
