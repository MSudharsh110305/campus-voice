from typing import Dict, Any
from config import Config

class PrivacyDetector:
    """Determines privacy level and visibility"""

    def __init__(self, config: Config):
        self.config = config

    def determine_privacy(self, complaint: str, llm_result: Dict[str, Any]) -> Dict[str, Any]:
        privacy_level = llm_result.get('privacy_level', 'public')
        authority_mentioned = llm_result.get('authority_mentioned', 'none')
        needs_bypass = llm_result.get('needs_bypass', False)

        text_lower = complaint.lower()
        has_sensitive = any(keyword in text_lower for keyword in self.config.privacy_keywords)
        if has_sensitive:
            privacy_level = 'confidential'

        visibility = self._determine_visibility(privacy_level, needs_bypass, authority_mentioned)
        return {
            'privacy_level': privacy_level,
            'authority_mentioned': authority_mentioned,
            'needs_bypass': needs_bypass,
            'visibility': visibility
        }

    def _determine_visibility(self, privacy_level: str, needs_bypass: bool, authority: str) -> str:
        if privacy_level == 'confidential':
            return "Only designated authorities and supervisors"
        elif privacy_level == 'private':
            if needs_bypass and authority in self.config.bypass_map:
                superior = self.config.bypass_map[authority]
                return f"Routed to {superior} and above (bypassing {authority})"
            else:
                return "Assigned authorities only"
        else:
            return "Assigned authorities + public voting enabled"
