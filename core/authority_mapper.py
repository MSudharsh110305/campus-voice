from typing import Dict, Any
from config import Config

class AuthorityMapper:
    """Maps complaints to correct authorities with bypass logic"""

    def __init__(self, config: Config):
        self.config = config

    def route_complaint(self, category: str, user_department: str,
                        needs_bypass: bool = False, mentioned_authority: str = "none") -> Dict[str, Any]:
        if category == "academic":
            return self._route_academic(user_department)
        elif category == "hostel":
            return self._route_hostel(needs_bypass, mentioned_authority)
        elif category == "infrastructure":
            return self._route_infrastructure()
        else:
            return self._route_infrastructure()

    def _route_academic(self, user_department: str) -> Dict[str, Any]:
        return {
            "final_authority": f"Head of Department - {user_department}",
            "routing_path": [f"📍 Routed to: Head of Department - {user_department}"],
            "bypass_applied": False,
            "reasoning": f"Academic complaint routed to user's department: {user_department}"
        }

    def _route_hostel(self, needs_bypass: bool, mentioned_authority: str) -> Dict[str, Any]:
        if not needs_bypass:
            return {
                "final_authority": "Hostel Warden",
                "routing_path": ["📍 Routed to: Hostel Warden"],
                "bypass_applied": False,
                "reasoning": "Standard hostel complaint routed to Warden"
            }

        if mentioned_authority == "warden":
            return {
                "final_authority": "Deputy Warden",
                "routing_path": [
                    "🚫 Complaint against: Hostel Warden",
                    "🔄 Bypassed to: Deputy Warden",
                    "📋 Reason: Avoid conflict of interest"
                ],
                "bypass_applied": True,
                "reasoning": "Complaint against Warden bypassed to Deputy Warden"
            }
        elif mentioned_authority == "deputy_warden":
            return {
                "final_authority": "Senior Deputy Warden",
                "routing_path": [
                    "🚫 Complaint against: Deputy Warden",
                    "🔄 Bypassed Warden (subordinate) and Deputy Warden",
                    "🔄 Routed to: Senior Deputy Warden",
                    "📋 Reason: Avoid conflict of interest in hierarchy"
                ],
                "bypass_applied": True,
                "reasoning": "Complaint against Deputy Warden bypassed to Senior Deputy Warden"
            }
        else:
            return {
                "final_authority": "Deputy Warden",
                "routing_path": [
                    "🔄 Authority bypass applied",
                    "📍 Routed to: Deputy Warden"
                ],
                "bypass_applied": True,
                "reasoning": "Bypass applied with unclear authority, routed to Deputy Warden"
            }

    def _route_infrastructure(self) -> Dict[str, Any]:
        return {
            "final_authority": "Administrative Officer (AO)",
            "routing_path": ["📍 Routed to: Administrative Officer (AO)"],
            "bypass_applied": False,
            "reasoning": "All infrastructure complaints go to Administrative Officer"
        }
