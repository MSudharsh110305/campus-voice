from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import os
import numpy as np
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import f1_score, classification_report
from scipy.sparse import csr_matrix
from joblib import dump, load

@dataclass
class ClassifierConfig:
    labels: Tuple[str, str, str] = ("hostel", "academic", "infrastructure")
    base_estimator: str = "logreg"  # "logreg" or "linearsvc"
    logreg_penalty: str = "l2"
    logreg_C: float = 1.0
    logreg_max_iter: int = 1000
    logreg_solver: str = "liblinear"
    logreg_class_weight: Optional[str] = "balanced"
    linsvc_C: float = 1.0
    linsvc_max_iter: int = 2000
    linsvc_class_weight: Optional[str] = "balanced"
    artifact_name: str = "classifier.joblib"
    min_confidence: float = 0.4
    max_labels: int = 2

class AuthorityClassifier:
    def __init__(self, config: Optional[ClassifierConfig] = None):
        self.config = config or ClassifierConfig()
        self._classifier: Optional[OneVsRestClassifier] = None
        self._label_binarizer = MultiLabelBinarizer(classes=self.config.labels)
        self._is_fitted = False

    def fit(self, X: csr_matrix, y_labels: List[List[str]]) -> "AuthorityClassifier":
        Y = self._label_binarizer.fit_transform(y_labels)
        self._classifier = OneVsRestClassifier(self._build_base_estimator())
        self._classifier.fit(X, Y)
        self._is_fitted = True
        return self

    def predict(self, X: csr_matrix) -> List[List[str]]:
        self._ensure_fitted()
        Y_pred = self._classifier.predict(X)
        return self._label_binarizer.inverse_transform(Y_pred)

    def predict_proba(self, X: csr_matrix) -> np.ndarray:
        self._ensure_fitted()
        if self.config.base_estimator == "logreg":
            probas = []
            for estimator in self._classifier.estimators_:
                proba = estimator.predict_proba(X)
                if proba.shape[1] == 1:
                    pos_proba = np.zeros(proba.shape[0])
                else:
                    pos_proba = proba[:, 1]
                probas.append(pos_proba)
            return np.column_stack(probas)
        else:
            return self._classifier.decision_function(X)

    def evaluate(self, X: csr_matrix, y_true: List[List[str]]) -> Dict[str, Any]:
        self._ensure_fitted()
        Y_true = self._label_binarizer.transform(y_true)
        Y_pred = self._classifier.predict(X)
        micro_f1 = f1_score(Y_true, Y_pred, average='micro', zero_division=0)
        macro_f1 = f1_score(Y_true, Y_pred, average='macro', zero_division=0)
        report = classification_report(Y_true, Y_pred, target_names=list(self.config.labels), zero_division=0, output_dict=True)
        return {
            "micro_f1": round(micro_f1, 4),
            "macro_f1": round(macro_f1, 4),
            "per_label_report": report,
            "labels": list(self.config.labels)
        }

    def save(self, dirpath: str) -> str:
        self._ensure_fitted()
        os.makedirs(dirpath, exist_ok=True)
        artifact_path = os.path.join(dirpath, self.config.artifact_name)
        bundle = {
            "config": asdict(self.config),
            "classifier": self._classifier,
            "label_binarizer": self._label_binarizer,
            "is_fitted": self._is_fitted
        }
        dump(bundle, artifact_path)
        return artifact_path

    @classmethod
    def load(cls, dirpath: str) -> "AuthorityClassifier":
        config = ClassifierConfig()
        artifact_path = os.path.join(dirpath, config.artifact_name)
        bundle = load(artifact_path)
        obj = cls(ClassifierConfig(**bundle["config"]))
        obj._classifier = bundle["classifier"]
        obj._label_binarizer = bundle["label_binarizer"]
        obj._is_fitted = bundle.get("is_fitted", True)
        return obj

    def _build_base_estimator(self):
        if self.config.base_estimator == "logreg":
            return LogisticRegression(
                C=self.config.logreg_C,
                penalty=self.config.logreg_penalty,
                solver=self.config.logreg_solver,
                max_iter=self.config.logreg_max_iter,
                class_weight=self.config.logreg_class_weight,
                random_state=42
            )
        elif self.config.base_estimator == "linearsvc":
            return LinearSVC(
                C=self.config.linsvc_C,
                max_iter=self.config.linsvc_max_iter,
                class_weight=self.config.linsvc_class_weight,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown base_estimator: {self.config.base_estimator}")

    def _ensure_fitted(self):
        if not self._is_fitted or self._classifier is None:
            raise RuntimeError("Classifier not fitted. Call fit() first.")

if __name__ == "__main__":

    from sklearn.feature_extraction.text import TfidfVectorizer

    texts = [
        "The hostel facilities are terrible and need improvement",
        "Academic curriculum is outdated and needs revision",
        "Infrastructure maintenance is poor in the main building",
        "Hostel staff is very supportive and helpful",
        "Academic schedule clashes with other events"
    ]
    labels = [
        ["hostel"],
        ["academic"],
        ["infrastructure"],
        ["hostel"],
        ["academic"]
    ]

    # Vectorize texts
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(texts)

    # Initialize classifier and fit
    classifier = AuthorityClassifier()
    classifier.fit(X, labels)

    # Predict on new samples
    new_texts = [
        "The hostel is dirty and noisy",
        "The academic programs are very comprehensive"
    ]
    X_new = vectorizer.transform(new_texts)
    preds = classifier.predict(X_new)
    print("Predicted labels:", preds)

    # Evaluate on training data (just for demo)
    eval_metrics = classifier.evaluate(X, labels)
    print("Evaluation metrics:", eval_metrics)

    # Save and load model
    save_path = classifier.save("/tmp/authority_classifier")
    print(f"Model saved to: {save_path}")

    loaded_classifier = AuthorityClassifier.load("/tmp/authority_classifier")
    loaded_preds = loaded_classifier.predict(X_new)
    print("Predictions from loaded model:", loaded_preds)

