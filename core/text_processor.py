# (Optional helper module; kept minimal or can be removed if unused)
# Provide string normalization or future NLP hooks if needed.

def normalize_whitespace(text: str) -> str:
    return " ".join(text.split()).strip()

# Add missing functions that __init__.py expects
def clean_text(text: str) -> str:
    """Clean and normalize text"""
    return normalize_whitespace(text)

def extract_metadata(text: str) -> dict:
    """Extract basic metadata from text"""
    return {
        "length": len(text),
        "words": len(text.split()),
        "sentences": text.count('.') + text.count('!') + text.count('?')
    }

class TextProcessor:
    """Simple text processor class"""
    
    @staticmethod
    def clean(text: str) -> str:
        return clean_text(text)
    
    @staticmethod
    def get_metadata(text: str) -> dict:
        return extract_metadata(text)
