from typing import Dict, Sequence

from sklearn.metrics import f1_score, precision_score, recall_score


def threshold_predictions(scores: Sequence[float], threshold: float = 0.5) -> Sequence[int]:
    return [1 if score >= threshold else 0 for score in scores]


def evaluate_similarity(y_true: Sequence[int], y_scores: Sequence[float], threshold: float = 0.5) -> Dict[str, float]:
    y_pred = threshold_predictions(y_scores, threshold)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    return {"precision": precision, "recall": recall, "f1_score": f1}
