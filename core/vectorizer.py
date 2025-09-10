from typing import Optional, Iterable, List
from dataclasses import dataclass, asdict
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.base import TransformerMixin
from scipy.sparse import csr_matrix
from joblib import dump, load

@dataclass
class VectorizerConfig:
    max_features: Optional[int] = 10000
    ngram_range: tuple = (1, 2)
    lowercase: bool = True
    stop_words: Optional[str] = "english"
    min_df: int = 2
    max_df: float = 0.85
    norm: str = "l2"
    use_idf: bool = True
    smooth_idf: bool = True
    sublinear_tf: bool = True
    token_pattern: str = r"(?u)\b\w\w+\b"
    artifact_name: str = "vectorizer.joblib"

class ComplaintVectorizer(TransformerMixin):
    def __init__(self, config: Optional[VectorizerConfig] = None):
        self.config = config or VectorizerConfig()
        self._vectorizer = None
        self._is_fitted = False

    def fit(self, texts: Iterable[str]) -> "ComplaintVectorizer":
        self._vectorizer = self._build_vectorizer()
        self._vectorizer.fit(texts)
        self._is_fitted = True
        return self

    def fit_transform(self, texts: Iterable[str]) -> csr_matrix:
        self._vectorizer = self._build_vectorizer()
        res = self._vectorizer.fit_transform(texts)
        self._is_fitted = True
        return res

    def transform(self, texts: Iterable[str]) -> csr_matrix:
        self._ensure_fitted()
        return self._vectorizer.transform(texts)

    def get_feature_names(self) -> List[str]:
        self._ensure_fitted()
        return list(self._vectorizer.get_feature_names_out())

    def get_vocab_size(self) -> int:
        return len(self.get_feature_names())

    def save(self, dirpath: str) -> str:
        self._ensure_fitted()
        os.makedirs(dirpath, exist_ok=True)
        artifact_path = os.path.join(dirpath, self.config.artifact_name)
        dump({
            "config": asdict(self.config),
            "vectorizer": self._vectorizer,
            "is_fitted": self._is_fitted
        }, artifact_path)
        return artifact_path

    @classmethod
    def load(cls, dirpath: str) -> "ComplaintVectorizer":
        config = VectorizerConfig()
        artifact_path = os.path.join(dirpath, config.artifact_name)
        bundle = load(artifact_path)
        obj = cls(VectorizerConfig(**bundle["config"]))
        obj._vectorizer = bundle["vectorizer"]
        obj._is_fitted = bundle.get("is_fitted", True)
        return obj

    def _build_vectorizer(self) -> TfidfVectorizer:
        return TfidfVectorizer(
            max_features=self.config.max_features,
            ngram_range=self.config.ngram_range,
            lowercase=self.config.lowercase,
            stop_words=self.config.stop_words,
            min_df=self.config.min_df,
            max_df=self.config.max_df,
            norm=self.config.norm,
            use_idf=self.config.use_idf,
            smooth_idf=self.config.smooth_idf,
            sublinear_tf=self.config.sublinear_tf,
            token_pattern=self.config.token_pattern
        )

    def _ensure_fitted(self):
        if not self._is_fitted or self._vectorizer is None:
            raise RuntimeError("Vectorizer not fitted. Call fit() or fit_transform() first.")

if __name__ == "__main__":
    import tempfile
    import shutil

    texts = [
        "The product is great, but the delivery was late.",
        "I am not happy with the quality of the product.",
        "Customer service was excellent and very helpful!",
        "The product broke after two uses, very disappointed.",
        "Delivery was on time, but the packaging was damaged."
    ]

    vectorizer = ComplaintVectorizer()

    # Test fit_transform
    X = vectorizer.fit_transform(texts)
    print("Shape after fit_transform:", X.shape)
    print("Feature names sample:", vectorizer.get_feature_names()[:10])
    print("Vocab size:", vectorizer.get_vocab_size())

    # Test transform on new data
    new_texts = [
        "I love the product quality!",
        "The delivery was late and the package was broken."
    ]
    X_new = vectorizer.transform(new_texts)
    print("Shape after transform:", X_new.shape)

    temp_dir = tempfile.mkdtemp()
    try:
        artifact_path = vectorizer.save(temp_dir)
        print("Saved vectorizer to:", artifact_path)
        loaded_vectorizer = ComplaintVectorizer.load(temp_dir)
        print("Loaded vectorizer vocab size:", loaded_vectorizer.get_vocab_size())
        X_loaded = loaded_vectorizer.transform(new_texts)
        print("Shape after transform with loaded vectorizer:", X_loaded.shape)

    finally:
        shutil.rmtree(temp_dir)