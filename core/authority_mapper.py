from typing import Dict, Any, Optional
from config import Config

class AuthorityMapper:
    """Maps complaints to correct authorities with bypass logic, cross-department handling, and disciplinary routing"""

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
            "3d printer", "cnc", "lathe", "printer", "workbench", "equipment",
            "instrument", "instruments", "department lab", "dept lab", "project lab"
        ]

        # Keywords that are building/facility-level → AO
        self.ao_infra_keywords = [
            "classroom", "class room", "toilet", "washroom", "corridor", "ceiling", "roof", "fan", "ac",
            "electricity", "power", "lighting", "ventilation", "plumbing", "water", "leak",
            "road", "parking", "gate", "lift", "elevator", "building", "block", "auditorium"
        ]

        # Sensitive/disciplinary indicators
        self.disciplinary_keywords = [
            "harass", "harassed", "harassment", "sexual", "abuse", "abused", "assault",
            "molest", "molestation", "discrimination", "ragging", "threat", "stalking",
            "inappropriate behavior", "misconduct"
        ]

        # Facility keywords that may be hostel or AO depending on residence
        self.context_facility_keywords = [
            "drinking water", "water", "bathroom", "toilet", "electricity", "power", "plumbing"
        ]

        # Building/block indicators
        self.building_block_keywords = [
            "block a", "block b", "block c", "main building", "admin block",
            "ece block", "cse block", "it block", "mechanical block", "civil block",
            "library", "auditorium", "seminar hall", "conference hall", "workshop",
            "canteen building", "sports complex"
        ]

        # Map block phrases to departments for asset inference
        self.block_to_dept = {
            'mechanical block': 'Mechanical Engineering',
            'ece block': 'Electronics & Communication Engineering',
            'cse block': 'Computer Science & Engineering',
            'it block': 'Information Technology',
            'civil block': 'Civil Engineering'
        }

    def route_complaint(
        self,
        category: str,
        user_department: str,
        needs_bypass: bool = False,
        mentioned_authority: str = "none",
        mentioned_department: Optional[str] = None,
        complaint_text: Optional[str] = None,
        user_residence: Optional[str] = None,
        needs_clarification: bool = False,
    ) -> Dict[str, Any]:
        """
        Determine final authority with explicit cross-department handling, hostel bypass rules,
        context-aware facilities, and disciplinary routing for sensitive cases.

        - category: 'academic' | 'hostel' | 'infrastructure' | 'disciplinary' (optional)
        - user_department: complainant's department
        - needs_bypass/mentioned_authority: for hostel authority conflicts
        - mentioned_department: explicit department referenced in the complaint (if any)
        - complaint_text: optional free text for heuristics (lab vs AO; sensitive)
        - user_residence: to disambiguate hostel vs AO when buildings aren't named
        - needs_clarification: if True, do not route; ask for exact location/ownership
        """
        # 0) Needs clarification: stop routing
        if needs_clarification:
            return {
                "final_authority": "Pending Clarification",
                "routing_path": [
                    "❓ Needs more information: location/ownership unspecified",
                    "⛔ Not routed to functional authority"
                ],
                "bypass_applied": False,
                "reasoning": "Insufficient information to determine owner"
            }

        txt = (complaint_text or "").lower()
        residence = (user_residence or "").lower()

        # 1) Force disciplinary routing on sensitive content
        if self._looks_disciplinary(txt):
            return self._route_disciplinary(user_department)

        # 2) Academic
        if category == "academic":
            return self._route_academic(user_department, mentioned_department, txt)

        # 3) Hostel
        if category == "hostel":
            return self._route_hostel(needs_bypass, mentioned_authority)

        # 4) Infrastructure (with context handling if needed)
        if category == "infrastructure":
            # Classroom is always AO
            if "classroom" in txt or "class room" in txt:
                return self._ao_route("Classroom issues are facility-level → AO")

            # Department lab/equipment overrides AO even when a block is mentioned
            if any(k in txt for k in self.lab_like_keywords):
                target = self._normalize_department(mentioned_department) or self._infer_department_from_block(txt)
                if target:
                    return {
                        "final_authority": f"Head of Department - {target}",
                        "routing_path": [f"📍 Routed to: Head of Department - {target}"],
                        "bypass_applied": False,
                        "reasoning": "Department lab/equipment issue routed to the respective HOD"
                    }

            # If explicit building mentioned → AO
            if self._mentions_building_or_block(txt):
                return self._ao_route("Specific building/block mentioned → AO")

            # Hostel-context facilities without block names and user in hostel → Warden
            if self._mentions_context_facilities(txt) and ('hostel' in residence or residence.startswith('hostel')):
                return {
                    "final_authority": "Hostel Warden",
                    "routing_path": ["📍 Routed to: Hostel Warden"],
                    "bypass_applied": False,
                    "reasoning": "Hostel resident with facility issue (no building specified) → Warden"
                }

            # Otherwise standard infra routing (default AO)
            return self._route_infrastructure(txt, mentioned_department)

        # 5) Fallback: default to infrastructure rules
        return self._route_infrastructure(txt, mentioned_department)

    # ------------------------ Disciplinary ------------------------

    def _route_disciplinary(self, user_department: str) -> Dict[str, Any]:
        return {
            "final_authority": "Student Counselor / Disciplinary Committee",
            "routing_path": [
                "🔒 Sensitive content detected",
                "📍 Routed to: Student Counselor / Disciplinary Committee",
                f"ℹ️ Department context: {user_department}"
            ],
            "bypass_applied": False,
            "reasoning": "Harassment/abuse/ragging-type complaint requires confidential disciplinary handling"
        }

    # ------------------------ Academic ------------------------

    def _route_academic(
        self,
        user_department: str,
        mentioned_department: Optional[str],
        complaint_text: str,
    ) -> Dict[str, Any]:
        target_dept = self._normalize_department(mentioned_department) or self._normalize_department(user_department)
        return {
            "final_authority": f"Head of Department - {target_dept}",
            "routing_path": [f"📍 Routed to: Head of Department - {target_dept}"],
            "bypass_applied": False,
            "reasoning": f"Academic complaint routed to department: {target_dept}"
        }

    # ------------------------ Hostel ------------------------

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
        complaint_text: str,
        mentioned_department: Optional[str],
    ) -> Dict[str, Any]:
        txt = complaint_text

        if any(k in txt for k in self.lab_like_keywords):
            target_dept = self._normalize_department(mentioned_department)
            if target_dept:
                return {
                    "final_authority": f"Head of Department - {target_dept}",
                    "routing_path": [f"📍 Routed to: Head of Department - {target_dept}"],
                    "bypass_applied": False,
                    "reasoning": "Department lab/equipment issue routed to the respective HOD"
                }

        if any(k in txt for k in self.ao_infra_keywords):
            return self._ao_route("Facility/building-level infrastructure routed to AO")

        return self._ao_route("General infrastructure routed to AO")

    # ------------------------ Helpers ------------------------

    def _normalize_department(self, name: Optional[str]) -> Optional[str]:
        if not name:
            return None
        key = name.strip().lower()
        if key in self.dept_alias:
            return self.dept_alias[key]
        return name.strip()

    def _infer_department_from_block(self, txt: str) -> Optional[str]:
        for block_phrase, dept in self.block_to_dept.items():
            if block_phrase in txt:
                return dept
        return None

    def _looks_disciplinary(self, txt: str) -> bool:
        return any(k in txt for k in self.disciplinary_keywords)

    def _mentions_building_or_block(self, txt: str) -> bool:
        return any(b in txt for b in self.building_block_keywords)

    def _mentions_context_facilities(self, txt: str) -> bool:
        return any(k in txt for k in self.context_facility_keywords)

    def _ao_route(self, reason: str) -> Dict[str, Any]:
        return {
            "final_authority": "Administrative Officer (AO)",
            "routing_path": ["📍 Routed to: Administrative Officer (AO)"],
            "bypass_applied": False,
            "reasoning": reason
        }
