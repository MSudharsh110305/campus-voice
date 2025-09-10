import re
import unicodedata
from typing import Optional, Dict


class TextCleaner:
    def __init__(self):
        #patterns 
        self.punctuation_pattern = re.compile(r'[^\w\s]')
        self.whitespace_pattern = re.compile(r'\s+')

        # Contractions
        self.contractions = {
            "don't": "do not",
            "won't": "will not",
            "can't": "cannot",
            "isn't": "is not",
            "wasn't": "was not",
            "doesn't": "does not",
            "didn't": "did not",
            "haven't": "have not",
            "hasn't": "has not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "couldn't": "could not",
            "it's": "it is",
            "i'm": "i am",
            "you're": "you are",
            "they're": "they are",
            "we're": "we are"
        }

    def clean(self, text: Optional[str]) -> str:
        if not text or not isinstance(text, str):
            return ""

        # Unicode normalization
        text = unicodedata.normalize('NFKD', text)
        # Lowercase and strip
        text = text.lower().strip()
        # Expand contractions
        text = self._expand_contractions(text)
        # Remove punctuation
        text = self.punctuation_pattern.sub(' ', text)
        # Remove all digits (fix)
        text = re.sub(r'\d+', '', text)
        # Normalize whitespaces
        text = self.whitespace_pattern.sub(' ', text).strip()

        return text


    def _expand_contractions(self, text: str) -> str:
        for contraction, expansion in self.contractions.items():
            text = text.replace(contraction, expansion)
        return text

    def extract_keywords(self, text: Optional[str]) -> Dict[str, float]:
        cleaned = self.clean(text)
        words = cleaned.split()
        total_chars = sum(len(word) for word in words)
        print("Words:", words)
        print("Char lengths:", [len(w) for w in words])
        print("Total chars:", total_chars)

        return {
            'word_count': len(words),
            'char_count': total_chars,
            'avg_word_length': total_chars / max(len(words), 1)
        }
        

cleaner = TextCleaner()


def clean_text(text: Optional[str]) -> str:
    return cleaner.clean(text)



if __name__ == "__main__":
    test_input = "Despite the CEO's insistence, they couldn't finalize the deal—it's been postponed until Q4 2025 due to unforeseen issues in the Asia-Pacific region, don't you think?"
    print("Cleaned text:")
    print(clean_text(test_input))
    print("\nKeyword stats:")
    print(cleaner.extract_keywords(test_input))
