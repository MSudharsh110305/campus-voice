from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np

@dataclass
class PostprocessConfig:
    min_confidence: float = 0.4
    high_confidence: float = 0.7
    max_labels: int = 2
    tie_delta: float = 0.05
    default_authority: str = "infrastructure"
    force_at_least_one: bool = True

@dataclass
class PostprocessResult:
    authorities: List[str]
    confidences: Dict[str, float]
    confidence_level: str  # "high", "medium", "low"
    fallback_applied: bool
    tie_broken: bool
    notes: List[str]

class PostProcessor:
    def __init__(self, config: Optional[PostprocessConfig] = None):
        self.config = config or PostprocessConfig()
        self.labels = ["hostel", "academic", "infrastructure"]

    def process(self, scores: np.ndarray) -> PostprocessResult:
        if len(scores) != len(self.labels):
            raise ValueError(f"Expected {len(self.labels)} scores, got {len(scores)}")

        notes = []
        tie_broken = False
        fallback_applied = False

        score_pairs = list(zip(self.labels, scores))
        score_pairs.sort(key=lambda x: x[1], reverse=True)

        confidences = {label: float(score) for label, score in score_pairs}

        above_threshold = [(label, score) for label, score in score_pairs if score >= self.config.min_confidence]

        if not above_threshold:
            authorities = [self.config.default_authority]
            fallback_applied = True
            notes.append(f"No predictions above {self.config.min_confidence}, using fallback: {self.config.default_authority}")
        else:
            authorities = []
            authorities.append(above_threshold[0][0])
            highest_score = above_threshold[0][1]
            for label, score in above_threshold[1:]:
                if len(authorities) >= self.config.max_labels:
                    break
                if (highest_score - score) <= self.config.tie_delta:
                    authorities.append(label)
                    tie_broken = True
                    notes.append(f"Added {label} due to tie (Δ={highest_score-score:.3f})")
                else:
                    break

        max_confidence = max(scores)
        if max_confidence >= self.config.high_confidence:
            confidence_level = "high"
        elif max_confidence >= self.config.min_confidence:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        if self.config.force_at_least_one and not authorities:
            authorities = [self.config.default_authority]
            fallback_applied = True
            notes.append("Forced at least one authority assignment")

        return PostprocessResult(
            authorities=authorities,
            confidences=confidences,
            confidence_level=confidence_level,
            fallback_applied=fallback_applied,
            tie_broken=tie_broken,
            notes=notes
        )

    def batch_process(self, scores_batch: np.ndarray) -> List[PostprocessResult]:
        if scores_batch.ndim != 2 or scores_batch.shape[1] != len(self.labels):
            raise ValueError(f"Expected shape (n_samples, {len(self.labels)}), got {scores_batch.shape}")
        return [self.process(scores) for scores in scores_batch]

    def get_confidence_stats(self, results: List[PostprocessResult]) -> Dict[str, Any]:
        if not results:
            return {}
        confidence_levels = [r.confidence_level for r in results]
        fallback_count = sum(1 for r in results if r.fallback_applied)
        tie_count = sum(1 for r in results if r.tie_broken)
        all_authorities = []
        for r in results:
            all_authorities.extend(r.authorities)
        authority_counts = {}
        for auth in self.labels:
            authority_counts[auth] = all_authorities.count(auth)
        return {
            "total_predictions": len(results),
            "confidence_distribution": {
                "high": confidence_levels.count("high"),
                "medium": confidence_levels.count("medium"),
                "low": confidence_levels.count("low")
            },
            "fallback_applied": fallback_count,
            "ties_broken": tie_count,
            "authority_distribution": authority_counts,
            "avg_authorities_per_complaint": len(all_authorities) / len(results) if results else 0
        }
if __name__ == "__main__":
    import numpy as np

    # Example scores for 3 samples and 3 labels: ["hostel", "academic", "infrastructure"]
    sample_scores = np.array([
        [0.8, 0.3, 0.5],  # high confidence hostel, infrastructure medium, academic low
        [0.35, 0.45, 0.4], # all around min_confidence, academic slightly higher
        [0.2, 0.1, 0.15]   # all below min_confidence
    ])

    postprocessor = PostProcessor()

    # Process single samples
    for i, scores in enumerate(sample_scores):
        result = postprocessor.process(scores)
        print(f"Sample {i+1}:")
        print(f"  Authorities: {result.authorities}")
        print(f"  Confidences: {result.confidences}")
        print(f"  Confidence level: {result.confidence_level}")
        print(f"  Fallback applied: {result.fallback_applied}")
        print(f"  Tie broken: {result.tie_broken}")
        if result.notes:
            print(f"  Notes: {result.notes}")
        print()

    # Batch process
    batch_results = postprocessor.batch_process(sample_scores)
    stats = postprocessor.get_confidence_stats(batch_results)
    print("Batch confidence stats:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
