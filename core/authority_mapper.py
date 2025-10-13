from typing import Dict, Any, Optional
from config import Config

class AuthorityMapper:
    """Maps complaints to correct authorities with bypass logic and cross-department handling"""

    def __init__(self, config: Config):
        self.config = config
        # Canonical department names map (short → full) for robustness
        self.dept_alias = {
            "cse": "Computer Science & Engineering",
            "ece": "Electronics & Communication Engineering",
            "it": "Information Technology",
            "eee": "Electrical & Electronics Engineering",
            "ei": "Electronics & Instrumentation Engineering",
            "e&i": "Electronics & Instrumentation Engineering",
            "mech": "Mechanical Engineering",
            "mechanical": "Mechanical Engineering",
            "civil": "Civil Engineering",
            "biomedical": "Biomedical Engineering",
            "aero": "Aeronautical Engineering",
            "ai&ds": "Artificial Intelligence and Data Science",
            "aids": "Artificial Intelligence and Data Science",
            "robotics": "Robotics and Automation",
            "mba": "Management Studies",
            "management": "Management Studies",
        }

        # Keywords that indicate department lab/resources → Academic authority
        self.lab_like_keywords = [
            "lab", "laboratory", "oscilloscope", "soldering", "arduino", "raspberry",
            "3d printer", "printer", "workbench", "equipment", "instrument", "instruments",
            "department lab", "dept lab", "project lab"
        ]

        # Keywords that are building/facility-level → AO
        self.ao_infra_keywords = [
            "classroom", "toilet", "washroom", "corridor", "ceiling", "roof", "fan", "ac",
            "electricity", "power", "lighting", "ventilation", "plumbing", "water", "leak",
            "road", "parking", "gate", "lift", "elevator", "building", "block", "auditorium"
        ]

    def route_complaint(
        self,
        category: str,
        user_department: str,
        needs_bypass: bool = False,
        mentioned_authority: str = "none",
        mentioned_department: Optional[str] = None,
        complaint_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Determine final authority with explicit cross-department handling and hostel bypass rules.

        - category: 'academic' | 'hostel' | 'infrastructure'
        - user_department: complainant's department
        - needs_bypass/mentioned_authority: set when the complaint targets hostel authorities
        - mentioned_department: explicit department referenced in the complaint (if any)
        - complaint_text: optional free text for heuristics (lab vs AO)
        """
        if category == "academic":
            return self._route_academic(user_department, mentioned_department, complaint_text)
        elif category == "hostel":
            return self._route_hostel(needs_bypass, mentioned_authority)
        elif category == "infrastructure":
            return self._route_infrastructure(complaint_text, mentioned_department)
        else:
            return self._route_infrastructure(complaint_text, mentioned_department)

    # ------------------------ Academic ------------------------

    def _route_academic(
        self,
        user_department: str,
        mentioned_department: Optional[str],
        complaint_text: Optional[str],
    ) -> Dict[str, Any]:
        """
        Academic complaints:
        - If another department is explicitly mentioned (e.g., ECE), route to that department's HOD.
        - Else default to user's department HOD.
        - Labs are always academic (never AO), even if the word 'infrastructure' appears.
        """
        target_dept = self._normalize_department(mentioned_department) or self._normalize_department(user_department)

        return {
            "final_authority": f"Head of Department - {target_dept}",
            "routing_path": [f"📍 Routed to: Head of Department - {target_dept}"],
            "bypass_applied": False,
            "reasoning": f"Academic complaint routed to department: {target_dept}"
        }

    # ------------------------ Hostel ------------------------

    def _route_hostel(self, needs_bypass: bool, mentioned_authority: str) -> Dict[str, Any]:
        """
        Hostel complaints with bypass rules:
        - If no bypass → Warden
        - If complaint about Warden → route to Deputy Warden
        - If complaint about Deputy Warden → bypass both and route to Senior Deputy Warden
        """
        if not needs_bypass:
            return {
                "final_authority": "Hostel Warden",
                "routing_path": ["📍 Routed to: Hostel Warden"],
                "bypass_applied": False,
                "reasoning": "Standard hostel complaint routed to Warden"
            }

        # Apply explicit authority bypass
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

        if mentioned_authority == "deputy_warden":
            return {
                "final_authority": "Senior Deputy Warden",
                "routing_path": [
                    "🚫 Complaint against: Deputy Warden",
                    "🔄 Bypassed Warden and Deputy Warden",
                    "📍 Routed to: Senior Deputy Warden",
                    "📋 Reason: Avoid conflict of interest in hierarchy"
                ],
                "bypass_applied": True,
                "reasoning": "Complaint against Deputy Warden routed to Senior Deputy Warden"
            }

        # Fallback when bypass is requested but unclear target
        return {
            "final_authority": "Deputy Warden",
            "routing_path": [
                "🔄 Authority bypass applied",
                "📍 Routed to: Deputy Warden"
            ],
            "bypass_applied": True,
            "reasoning": "Bypass applied with unclear authority; routed to Deputy Warden"
        }

    # ------------------------ Infrastructure ------------------------

    def _route_infrastructure(
        self,
        complaint_text: Optional[str],
        mentioned_department: Optional[str],
    ) -> Dict[str, Any]:
        """
        Infrastructure complaints:
        - Department lab/equipment issues → route to that department's HOD.
        - Building/facility issues (classrooms, plumbing, electricity, roads, buildings) → AO.
        - If a department is named and text indicates lab/resources, route to that department HOD.
        """
        txt = (complaint_text or "").lower()

        # If lab-like terms appear → HOD of mentioned department (or fallback to user's dept handled upstream)
        if any(k in txt for k in self.lab_like_keywords):
            target_dept = self._normalize_department(mentioned_department)
            if target_dept:
                return {
                    "final_authority": f"Head of Department - {target_dept}",
                    "routing_path": [f"📍 Routed to: Head of Department - {target_dept}"],
                    "bypass_applied": False,
                    "reasoning": "Department lab/equipment issue routed to the respective HOD"
                }

        # If classic AO infrastructure keywords → AO
        if any(k in txt for k in self.ao_infra_keywords):
            return {
                "final_authority": "Administrative Officer (AO)",
                "routing_path": ["📍 Routed to: Administrative Officer (AO)"],
                "bypass_applied": False,
                "reasoning": "Facility/building-level infrastructure routed to AO"
            }

        # Default infrastructure → AO
        return {
            "final_authority": "Administrative Officer (AO)",
            "routing_path": ["📍 Routed to: Administrative Officer (AO)"],
            "bypass_applied": False,
            "reasoning": "General infrastructure routed to AO"
        }

    # ------------------------ Helpers ------------------------

    def _normalize_department(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        key = name.strip().lower()
        # Match alias first
        if key in self.dept_alias:
            return self.dept_alias[key]
        # If already a full name, return as-is
        return name.strip()
