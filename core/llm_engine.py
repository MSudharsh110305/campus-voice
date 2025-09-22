import requests
import json
import time
import re
import base64
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from config import Config

@dataclass
class OllamaResponse:
    success: bool
    content: str
    model: str
    elapsed: float
    error: Optional[str] = None

class OllamaClient:
    """Ollama client for LLM communication"""
    
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.ollama_host
        self.timeout = config.ollama_timeout
        self.available_models = self._get_available_models()
        
    def _get_available_models(self) -> List[str]:
        """Get available models from Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
        except Exception:
            pass
        return []
    
    def set_model(self, model_name: str, is_multimodal: bool = False):
        """Set the current model"""
        self.config.current_model = model_name
        self.config.is_multimodal = is_multimodal
    
    def generate(self, prompt: str, image_data: Optional[str] = None) -> OllamaResponse:
        """Generate response from LLM"""
        if not self.config.current_model:
            return OllamaResponse(False, "", "", 0, "No model selected")
        
        payload = {
            "model": self.config.current_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1}
        }
        
        # Add image if provided and model supports it
        if image_data and self.config.is_multimodal:
            payload["images"] = [image_data]
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            elapsed = time.time() - start_time
            
            return OllamaResponse(
                success=True,
                content=result.get('response', '').strip(),
                model=self.config.current_model,
                elapsed=elapsed
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            return OllamaResponse(
                success=False,
                content="",
                model=self.config.current_model,
                elapsed=elapsed,
                error=str(e)
            )
    
    def classify_complaint(self, complaint: str, image_data: Optional[str] = None) -> Dict[str, Any]:
        """Classify complaint into one of three categories"""
        
        prompt = f"""Analyze this student complaint and classify it into ONE category:

COMPLAINT: "{complaint}"
"""
        
        if image_data:
            prompt += "\nIMAGE: Analyze the provided image for additional context.\n"
        
        prompt += """
Classify into EXACTLY ONE category:
- hostel: accommodation, rooms, mess, food, warden, deputy warden, hostel facilities
- academic: professors, classes, exams, grades, curriculum, departments, teaching
- infrastructure: buildings, facilities, parking, library, maintenance, technology, systems

Respond with JSON:
{
    "category": "hostel|academic|infrastructure",
    "confidence": "high|medium|low",
    "reasoning": "brief explanation"
}"""

        response = self.generate(prompt, image_data)
        
        if response.success:
            try:
                result = json.loads(response.content)
                # Validate category
                if result.get('category') in ['hostel', 'academic', 'infrastructure']:
                    return result
            except json.JSONDecodeError:
                pass
        
        # Fallback classification using keywords
        return self._fallback_classify(complaint)
    
    def detect_authority_bypass(self, complaint: str, category: str, image_data: Optional[str] = None) -> Dict[str, Any]:
        """Detect if complaint is against specific authority and needs bypass"""
        
        if category != "hostel":
            return {
                "needs_bypass": False,
                "mentioned_authority": "none",
                "reasoning": "Only hostel complaints can have authority bypass"
            }
        
        prompt = f"""Analyze this hostel complaint for authority bypass needs:

COMPLAINT: "{complaint}"
"""
        
        if image_data:
            prompt += "\nIMAGE: Consider image content.\n"
        
        prompt += """
Determine if complaint is AGAINST a specific authority:

{
    "needs_bypass": true/false,
    "mentioned_authority": "none|warden|deputy_warden",
    "reasoning": "explanation"
}

BYPASS RULES:
- needs_bypass: true if complaint CRITICIZES/COMPLAINS ABOUT an authority
- mentioned_authority: WHO is being complained about
- Look for negative context: "ignoring", "rude", "bribery", "corruption", "not helping"

Examples:
- "warden is rude" → needs_bypass: true, mentioned_authority: "warden"
- "deputy warden not responding" → needs_bypass: true, mentioned_authority: "deputy_warden"
- "hostel food is bad" → needs_bypass: false, mentioned_authority: "none"
"""

        response = self.generate(prompt, image_data)
        
        if response.success:
            try:
                result = json.loads(response.content)
                if isinstance(result.get('needs_bypass'), bool):
                    return result
            except json.JSONDecodeError:
                pass
        
        # Fallback bypass detection
        return self._fallback_bypass_detection(complaint)
    
    def _fallback_classify(self, complaint: str) -> Dict[str, Any]:
        """Fallback classification using keyword matching"""
        complaint_lower = complaint.lower()
        scores = {}
        
        for category, keywords in self.config.authority_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in complaint_lower)
            scores[category] = matches
        
        # Get category with highest score
        best_category = max(scores, key=scores.get)
        confidence = "high" if scores[best_category] >= 2 else "medium" if scores[best_category] >= 1 else "low"
        
        return {
            "category": best_category,
            "confidence": confidence,
            "reasoning": f"Keyword-based classification: {scores[best_category]} matches"
        }
    
    def _fallback_bypass_detection(self, complaint: str) -> Dict[str, Any]:
        """Fallback bypass detection using keywords"""
        complaint_lower = complaint.lower()
        
        # Check for authority mentions
        mentioned = "none"
        if "deputy warden" in complaint_lower:
            mentioned = "deputy_warden"
        elif "warden" in complaint_lower:
            mentioned = "warden"
        
        # Check for negative context
        negative_indicators = ["bribery", "corruption", "ignoring", "rude", "not helping", "not responding"]
        needs_bypass = mentioned != "none" and any(indicator in complaint_lower for indicator in negative_indicators)
        
        return {
            "needs_bypass": needs_bypass,
            "mentioned_authority": mentioned,
            "reasoning": f"Keyword-based detection: authority={mentioned}, negative_context={needs_bypass}"
        }
