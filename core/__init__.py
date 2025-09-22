"""
Campus Voice AI Core Module v2.0
Hybrid Framework using Ollama LLM + Rule-based Classification
"""

from config import Config
from text_processor import TextProcessor, clean_text, extract_metadata
from llm_engine import OllamaClient
from hybrid_classifier import HybridClassifier
from authority_mapper import AuthorityMapper
from privacy_detector import PrivacyDetector
from priority_scorer import PriorityScorer

__version__ = "2.0"
__all__ = [
    "Config", "TextProcessor", "clean_text", "extract_metadata",
    "OllamaClient", "HybridClassifier", "AuthorityMapper",
    "PrivacyDetector", "PriorityScorer"
]
