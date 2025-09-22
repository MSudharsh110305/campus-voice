import re
import unicodedata
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class TextMetadata:
    word_count: int
    char_count: int
    urgency_indicators: int
    has_questions: bool
    has_time_context: bool
    avg_word_length: float

class TextProcessor:
    """Enhanced text processor for campus complaints"""
    
    def __init__(self):
        self.punctuation_pattern = re.compile(r'[^\w\s]')
        self.whitespace_pattern = re.compile(r'\s+')
        
        # Contractions dictionary
        self.contractions = {
            "don't": "do not", "won't": "will not", "can't": "cannot",
            "isn't": "is not", "wasn't": "was not", "doesn't": "does not",
            "didn't": "did not", "haven't": "have not", "hasn't": "has not",
            "shouldn't": "should not", "wouldn't": "would not", "couldn't": "could not",
            "it's": "it is", "i'm": "i am", "you're": "you are",
            "they're": "they are", "we're": "we are"
        }
        
        # Campus abbreviations
        self.abbreviations = {
            "hod": "head of department",
            "ao": "administrative officer",
            "ac": "air conditioning", 
            "wifi": "wireless internet",
            "cse": "computer science engineering",
            "ece": "electronics communication engineering"
        }

    def clean(self, text: Optional[str]) -> str:
        """Clean and normalize text"""
        if not text or not isinstance(text, str):
            return ""
        
        # Unicode normalization
        text = unicodedata.normalize('NFKD', text)
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Expand contractions
        text = self._expand_contractions(text)
        
        # Expand abbreviations  
        text = self._expand_abbreviations(text)
        
        # Remove punctuation
        text = self.punctuation_pattern.sub(' ', text)
        
        # Remove standalone numbers
        text = re.sub(r'\b\d+\b', '', text)
        
        # Normalize whitespace
        text = self.whitespace_pattern.sub(' ', text).strip()
        
        return text

    def extract_metadata(self, text: str) -> TextMetadata:
        """Extract metadata from text"""
        cleaned = self.clean(text)
        words = cleaned.split()
        
        # Count urgency indicators
        urgency_words = ["urgent", "emergency", "immediate", "asap", "critical"]
        urgency_count = sum(1 for word in words if word in urgency_words)
        
        # Detect questions
        question_words = ["why", "how", "what", "when", "where", "which"]
        has_questions = any(word in words for word in question_words)
        
        # Detect time context
        time_words = ["today", "yesterday", "now", "currently", "recently"]
        has_time_context = any(word in words for word in time_words)
        
        return TextMetadata(
            word_count=len(words),
            char_count=len(cleaned),
            urgency_indicators=urgency_count,
            has_questions=has_questions,
            has_time_context=has_time_context,
            avg_word_length=sum(len(w) for w in words) / max(len(words), 1)
        )

    def _expand_contractions(self, text: str) -> str:
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        return text

    def _expand_abbreviations(self, text: str) -> str:
        for abbrev, expansion in self.abbreviations.items():
            pattern = r'\b' + re.escape(abbrev) + r'\b'
            text = re.sub(pattern, expansion, text)
        return text

# Convenience functions
processor = TextProcessor()

def clean_text(text: Optional[str]) -> str:
    return processor.clean(text)

def extract_metadata(text: str) -> TextMetadata:
    return processor.extract_metadata(text)
