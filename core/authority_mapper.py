"""
Authority Mapper - Smart complaint routing with bypass logic
Handles cross-department, hostel hierarchy, and disciplinary routing
"""

from typing import Dict, Any, Optional
from core.config import Config


class AuthorityMapper:
    """
    Maps complaints to correct authorities with intelligent routing.
    - Cross-department handling
    - Hostel hierarchy bypass
    - Disciplinary escalation
    - Context-aware facility routing
    """

    def __init__(self, config: Config):
        """Initialize with configuration."""
        self.config = config
        
        # Department aliases
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
            "management": "Management Studies"
        }
        
        # Lab/equipment keywords
        self.lab_like_keywords = [
            'lab', 'laboratory', 'oscilloscope', 'soldering', 'arduino',
            'raspberry', '3d printer', 'cnc', 'lathe', 'printer',
            'workbench', 'equipment', 'instrument', 'instruments',
            'department lab', 'dept lab', 'project lab', 'multimeter',
            'voltmeter', 'microscope', 'test bench'
        ]
        
        # AO infrastructure keywords
        self.ao_infra_keywords = [
            'classroom', 'class room', 'toilet', 'washroom', 'restroom',
            'corridor', 'ceiling', 'roof', 'fan', 'ac', 'air conditioning',
            'electricity', 'power', 'lighting', 'ventilation', 'plumbing',
            'water supply', 'leak', 'drainage', 'road', 'parking', 'gate',
            'lift', 'elevator', 'building', 'block', 'auditorium', 'stairs',
            'door', 'window', 'wall', 'floor', 'paint', 'maintenance'
        ]
        
        # Disciplinary keywords (ragging, harassment, personal issues)
        self.disciplinary_keywords = [
            'harass', 'harassed', 'harassment', 'sexual', 'abuse', 'abused',
            'assault', 'molest', 'molestation', 'discrimination', 'ragging',
            'threat', 'stalking', 'inappropriate behavior', 'misconduct',
            'bully', 'bullying', 'intimidate', 'violent', 'violence',
            'personal issue', 'personal problem', 'very personal', 'private matter',
            'mental health', 'depression', 'anxiety', 'suicide', 'self harm'
        ]
        
        # Context facility keywords
        self.context_facility_keywords = [
            'drinking water', 'water', 'bathroom', 'toilet', 'restroom',
            'electricity', 'power', 'plumbing', 'drainage'
        ]
        
        # Building/block keywords
        self.building_block_keywords = [
            'block a', 'block b', 'block c', 'main building', 'admin block',
            'ece block', 'cse block', 'it block', 'mechanical block', 'civil block',
            'eee block', 'library', 'auditorium', 'seminar hall', 'conference hall',
            'workshop', 'canteen building', 'sports complex', 'g block', 'f block'
        ]
        
        # Hostel keywords
        self.hostel_keywords = [
            'hostel', 'warden', 'deputy warden', 'mess', 'curfew',
            'room no', 'bed', 'dormitory', 'hostel room'
        ]
        
        # Block to department mapping
        self.block_to_dept = {
            'mechanical block': 'Mechanical Engineering',
            'ece block': 'Electronics & Communication Engineering',
            'cse block': 'Computer Science & Engineering',
            'it block': 'Information Technology',
            'civil block': 'Civil Engineering',
            'eee block': 'Electrical & Electronics Engineering'
        }

    def route_complaint(
        self,
        category: str,
        user_department: str,
        complaint_text: Optional[str] = None,
        needs_bypass: bool = False,
        mentioned_authority: str = 'none',
        mentioned_department: Optional[str] = None,
        requires_image: bool = False,
        image_reason: str = ''
    ) -> Dict[str, Any]:
        """
        Determine final authority with comprehensive routing logic.
        
        Returns:
            Dict with final_authority, routing_path, routing_reasoning, etc.
        """
        txt = (complaint_text or '').lower()
        
        # Priority 1: Disciplinary/Sensitive content
        if self._looks_disciplinary(txt):
            return self._route_disciplinary(user_department)
        
        # Priority 2: Academic
        if category == 'academic':
            return self._route_academic(user_department, mentioned_department, txt)
        
        # Priority 3: Hostel
        if category == 'hostel':
            return self._route_hostel(needs_bypass, mentioned_authority, txt)
        
        # Priority 4: Infrastructure
        if category == 'infrastructure':
            return self._route_infrastructure_smart(txt, user_department, mentioned_department, '')
        
        # Fallback
        return self._route_infrastructure_smart(txt, user_department, mentioned_department, '')

    def _route_disciplinary(self, user_department: str) -> Dict[str, Any]:
        """Route sensitive/disciplinary complaints to counselor ONLY (not principal)."""
        return {
            'final_authority': 'Student Counselor / Disciplinary Committee',
            'routing_path': [
                'Sensitive content detected (harassment/abuse/ragging/personal issues)',
                'Routed to Student Counselor / Disciplinary Committee ONLY',
                f'Department context: {user_department}',
                'Confidential handling required - Principal can view but not assigned'
            ],
            'routing_reasoning': 'Sensitive complaint (ragging/harassment/personal issues) routed exclusively to Student Counselor / Disciplinary Committee for confidential handling',
            'hidden_from': [],  # Principal can see all, but complaint is assigned to counselor only
            'bypass_applied': False,
            'escalated_to': None
        }

    def _route_academic(self, user_department: str, mentioned_department: Optional[str], complaint_text: str) -> Dict[str, Any]:
        """Route academic complaints to appropriate HOD."""
        # Try to identify target department
        target_dept = None
        
        if mentioned_department:
            target_dept = self._normalize_department(mentioned_department)
        
        if not target_dept:
            target_dept = self._infer_department_from_block(complaint_text)
        
        if not target_dept:
            target_dept = self._normalize_department(user_department)
        
        if not target_dept:
            target_dept = user_department
        
        return {
            'final_authority': f'Head of Department - {target_dept}',
            'routing_path': [
                f'Routed to Head of Department - {target_dept}',
                f'Department: {target_dept}'
            ],
            'routing_reasoning': f'Academic complaint routed to {target_dept} HOD',
            'hidden_from': [],
            'bypass_applied': False,
            'escalated_to': None
        }

    def _route_hostel(self, needs_bypass: bool, mentioned_authority: str, complaint_text: str) -> Dict[str, Any]:
        """Route hostel complaints with bypass logic."""
        if not needs_bypass:
            return {
                'final_authority': 'Hostel Warden',
                'routing_path': [
                    'Routed to Hostel Warden',
                    'Standard hostel complaint routing'
                ],
                'routing_reasoning': 'Standard hostel complaint routed to Warden',
                'hidden_from': [],
                'bypass_applied': False,
                'escalated_to': None
            }
        
        # Bypass logic
        if mentioned_authority == 'warden':
            return {
                'final_authority': 'Deputy Warden',
                'routing_path': [
                    'Complaint against Hostel Warden',
                    'Bypassed to Deputy Warden',
                    'Reason: Conflict of interest avoided'
                ],
                'routing_reasoning': 'Complaint against Warden bypassed to Deputy Warden',
                'hidden_from': ['Hostel Warden'],
                'bypass_applied': True,
                'escalated_to': 'Deputy Warden'
            }
        
        if mentioned_authority == 'deputy_warden':
            return {
                'final_authority': 'Senior Deputy Warden',
                'routing_path': [
                    'Complaint against Deputy Warden',
                    'Bypassed Warden and Deputy Warden',
                    'Routed to Senior Deputy Warden',
                    'Reason: Higher escalation for hierarchy conflict'
                ],
                'routing_reasoning': 'Complaint against Deputy Warden routed to Senior Deputy Warden',
                'hidden_from': ['Hostel Warden', 'Deputy Warden'],
                'bypass_applied': True,
                'escalated_to': 'Senior Deputy Warden'
            }
        
        return {
            'final_authority': 'Deputy Warden',
            'routing_path': [
                'Authority bypass applied',
                'Routed to Deputy Warden',
                'Default escalation for unclear bypass scenario'
            ],
            'routing_reasoning': 'Bypass applied with unclear authority defaulted to Deputy Warden',
            'hidden_from': [],
            'bypass_applied': True,
            'escalated_to': 'Deputy Warden'
        }

    def _route_infrastructure_smart(self, complaint_text: str, user_department: str, mentioned_department: Optional[str], user_residence: str) -> Dict[str, Any]:
        """Smart infrastructure routing with context awareness."""
        txt = complaint_text
        
        # Rule 1: Classroom is ALWAYS facility-level (AO)
        if 'classroom' in txt or 'class room' in txt:
            return self._ao_route('Classroom issues are facility-level (Administrative Officer)')
        
        # Rule 2: Department lab/equipment → HOD (overrides building mention)
        if any(k in txt for k in self.lab_like_keywords):
            target_dept = (self._normalize_department(mentioned_department) or 
                          self._infer_department_from_block(txt) or 
                          self._normalize_department(user_department))
            
            return {
                'final_authority': f'Head of Department - {target_dept}',
                'routing_path': [
                    'Department lab/equipment issue detected',
                    f'Routed to Head of Department - {target_dept}'
                ],
                'routing_reasoning': f'Department lab/equipment issue routed to {target_dept} HOD',
                'hidden_from': [],
                'bypass_applied': False,
                'escalated_to': None
            }
        
        # Rule 3: Explicit building/block mentioned → AO
        if self._mentions_building_or_block(txt):
            return self._ao_route('Specific building/block mentioned (Administrative Officer)')
        
        # Rule 4: Context facilities + hostel cues → Warden
        if self._mentions_context_facilities(txt):
            if any(h in txt for h in self.hostel_keywords):
                return {
                    'final_authority': 'Hostel Warden',
                    'routing_path': [
                        'Hostel facility issue detected',
                        'Routed to Hostel Warden'
                    ],
                    'routing_reasoning': 'Hostel facility (water/toilet/electricity) with hostel context → Warden',
                    'hidden_from': [],
                    'bypass_applied': False,
                    'escalated_to': None
                }
        
        # Rule 5: General infrastructure → AO
        if any(k in txt for k in self.ao_infra_keywords):
            return self._ao_route('Facility/building-level infrastructure (Administrative Officer)')
        
        # Default: Route to AO
        return self._ao_route('General infrastructure issue (Administrative Officer)')

    # Helper methods
    def _normalize_department(self, name: Optional[str]) -> Optional[str]:
        """Normalize department name."""
        if not name:
            return None
        
        key = name.strip().lower()
        
        if key in self.dept_alias:
            return self.dept_alias[key]
        
        return name.strip()

    def _infer_department_from_block(self, txt: str) -> Optional[str]:
        """Infer department from block mention."""
        for block_phrase, dept in self.block_to_dept.items():
            if block_phrase in txt:
                return dept
        return None

    def _looks_disciplinary(self, txt: str) -> bool:
        """Check if complaint contains disciplinary/sensitive keywords."""
        return any(k in txt for k in self.disciplinary_keywords)

    def _mentions_building_or_block(self, txt: str) -> bool:
        """Check if complaint mentions specific building/block."""
        return any(b in txt for b in self.building_block_keywords)

    def _mentions_context_facilities(self, txt: str) -> bool:
        """Check if complaint mentions context-sensitive facilities."""
        return any(k in txt for k in self.context_facility_keywords)

    def _ao_route(self, reason: str) -> Dict[str, Any]:
        """Standard AO routing with reasoning."""
        return {
            'final_authority': 'Administrative Officer (AO)',
            'routing_path': [
                'Routed to Administrative Officer (AO)',
                f'Reason: {reason}'
            ],
            'routing_reasoning': reason,
            'hidden_from': [],
            'bypass_applied': False,
            'escalated_to': None
        }
