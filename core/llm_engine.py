import json
from typing import Optional, Dict, Any

import requests
from config import Config

SYSTEM_PROMPT = """You are Campus Voice AI.
Tasks:
1) Understand complaint intent using text and optionally image description.
2) Decide one category: hostel | academic | infrastructure.
3) Apply rules:
   - If specific building mentioned (A/B/C/IT/ECE/Spark/CSE/Library/MBA/G/F/Main), treat as infrastructure.
   - Facilities like bathroom/drinking water exist in both; if hosteller and no building specified, treat as hostel.
   - Academics includes teaching quality, labs, department staff, exams, syllabus.
   - If a different department is explicitly named for an academic issue, route to that department.
4) For hostel authority targeting:
   - If complaint is about the Warden → needs_bypass=true and mentioned_authority="warden".
   - If complaint is about the Deputy Warden → needs_bypass=true and mentioned_authority="deputy_warden".
5) Provide a short reasoning and a confidence string (High/Medium/Low).
6) Provide a 'privacy_level' hint if content is sensitive.
7) If the text explicitly names a different department from the complainant (e.g., ECE, CSE, IT, Mechanical, Civil, EEE, E&I, Biomedical, Aeronautical, AI&DS, Robotics, MBA/Management),
   set target_department to that department's full name as used on campus; else null.

Return strict JSON with keys:
- category: "hostel" | "academic" | "infrastructure"
- mentioned_authority: "none" | "warden" | "deputy_warden"
- needs_bypass: boolean
- privacy_level: "public" | "private" | "confidential"
- authority_mentioned: same as mentioned_authority
- confidence: "High" | "Medium" | "Low"
- reasoning: string
- target_department: string or null
"""

REPHRASE_PROMPT = """Rephrase the complaint in formal, precise English suitable for an official portal.
- Keep it concise and respectful.
- Include user context (department, residence, gender if helpful) only when it clarifies.
- If academic, clarify course/staff/lab when provided.
- If infrastructure, include building/facility names found or inferred.
- If hostel subtle facilities from a hosteller, clarify hostel context.

Return only the rephrased single-paragraph text, no preface.
"""

class OllamaClient:
    def __init__(self, config: Config):
        self.cfg = config

    def _generate(self, prompt: str, images_b64: Optional[str] = None) -> str:
        payload = {
            "model": self.cfg.current_model,
            "prompt": prompt,
            "stream": False,
        }
        if images_b64 is not None and self.cfg.is_multimodal:
            payload["images"] = [images_b64]
        resp = requests.post(
            f"{self.cfg.ollama_host}/api/generate",
            json=payload,
            timeout=self.cfg.ollama_timeout
        )
        resp.raise_for_status()
        return resp.json().get("response", "")

    def classify_complaint(self, complaint: str, image_data: Optional[str]) -> Dict[str, Any]:
        payload = {"complaint": complaint}
        prompt = SYSTEM_PROMPT + "\n\n" + json.dumps(payload)
        raw = self._generate(prompt, images_b64=image_data)
        txt = raw.strip()
        start = txt.find("{")
        end = txt.rfind("}")
        if start == -1 or end == -1:
            return {
                "category": "infrastructure",
                "mentioned_authority": "none",
                "needs_bypass": False,
                "privacy_level": "public",
                "authority_mentioned": "none",
                "confidence": "Low",
                "reasoning": "Fallback due to parsing",
                "target_department": None
            }
        try:
            data = json.loads(txt[start:end+1])
        except Exception:
            data = {
                "category": "infrastructure",
                "mentioned_authority": "none",
                "needs_bypass": False,
                "privacy_level": "public",
                "authority_mentioned": "none",
                "confidence": "Low",
                "reasoning": "JSON parse error",
                "target_department": None
            }

        # Ensure required keys
        data.setdefault("category", "infrastructure")
        data.setdefault("mentioned_authority", "none")
        data.setdefault("authority_mentioned", data["mentioned_authority"])
        data.setdefault("needs_bypass", False)
        data.setdefault("privacy_level", "public")
        data.setdefault("confidence", "Medium")
        data.setdefault("reasoning", "LLM analysis")
        data.setdefault("target_department", None)

        # Normalize common department short forms to full names if present
        # This helps when the model outputs shorthand; adjust as per campus canonical names.
        dept_map = {
            "ece": "Electronics & Communication Engineering",
            "cse": "Computer Science & Engineering",
            "it": "Information Technology",
            "eee": "Electrical & Electronics Engineering",
            "e&i": "Electronics & Instrumentation Engineering",
            "ei": "Electronics & Instrumentation Engineering",
            "mech": "Mechanical Engineering",
            "mechanical": "Mechanical Engineering",
            "civil": "Civil Engineering",
            "ai&ds": "Artificial Intelligence and Data Science",
            "aids": "Artificial Intelligence and Data Science",
            "biomedical": "Biomedical Engineering",
            "aero": "Aeronautical Engineering",
            "mba": "Management Studies",
            "management": "Management Studies",
            "robotics": "Robotics and Automation"
        }
        td = data.get("target_department")
        if isinstance(td, str):
            key = td.strip().lower()
            if key in dept_map:
                data["target_department"] = dept_map[key]

        return data

    def detect_authority_bypass(self, complaint: str, category: str, image_data: Optional[str]) -> Dict[str, Any]:
        if category != "hostel":
            return {
                "needs_bypass": False,
                "mentioned_authority": "none",
                "reasoning": "Non-hostel complaint"
            }
        # Reuse classify to capture authority mentions
        data = self.classify_complaint(complaint, image_data)
        mentioned = data.get("mentioned_authority", "none")
        needs = data.get("needs_bypass", False)

        # Harden with keyword fallback
        low = complaint.lower()
        if "deputy warden" in low or ("deputy" in low and "warden" in low):
            mentioned = "deputy_warden"
            needs = True
        elif "warden" in low and "deputy" not in low:
            mentioned = "warden"
            needs = True

        reason = f"Complaint targets {mentioned}" if mentioned != "none" else "No specific authority targeted"
        return {
            "needs_bypass": bool(needs),
            "mentioned_authority": mentioned,
            "reasoning": reason
        }

    def rephrase_complaint(self, complaint: str, user_context: Dict[str, Any],
                           image_data: Optional[str], classification_hint: str) -> str:
        ctx = {
            "complaint": complaint,
            "user_context": user_context,
            "category": classification_hint
        }
        prompt = REPHRASE_PROMPT + "\n\n" + json.dumps(ctx)
        out = self._generate(prompt, images_b64=image_data)
        return out.strip()
