# (Optional helper module; kept minimal or can be removed if unused)
# Provide string normalization or future NLP hooks if needed.

def normalize_whitespace(text: str) -> str:
    return " ".join(text.split()).strip()
