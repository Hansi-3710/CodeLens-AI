"""
Trains a classifier that predicts *which model* generated a given piece of
code from its embedding/style features — quantifies how distinct each
model's "fingerprint" is. High cross-validated accuracy means the models
are stylistically distinguishable; near-chance accuracy means they're not.

Belongs to: backend/app/ml/
Phase: 6 (ML & Code Analysis)
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score


def train_model_fingerprint_classifier(
    features: list[list[float]], labels: list[str]
) -> dict:
    """features: one row per solution (embedding and/or complexity/style
    features concatenated). labels: the model name that generated it.

    Returns {"cv_accuracy": float, "cv_accuracy_std": float, "n_samples": int,
    "n_classes": int, "baseline_accuracy": float, "sufficient_data": bool}.

    Cross-validated, not a single train/test split — per-experiment sample
    sizes are often small (a handful of solutions per model), where a
    single split's accuracy is noisy and can mislead. baseline_accuracy is
    the accuracy from *always guessing the majority class*, since "78%
    accuracy" is only impressive relative to how skewed the label
    distribution is.
    """
    n_samples = len(labels)
    n_classes = len(set(labels))
    class_counts = {label: labels.count(label) for label in set(labels)}
    baseline_accuracy = max(class_counts.values()) / n_samples if n_samples else 0.0

    # Need at least as many samples per class as CV folds, and at least 2 classes.
    min_class_count = min(class_counts.values()) if class_counts else 0
    n_folds = min(5, min_class_count)
    sufficient_data = n_classes >= 2 and n_folds >= 2

    if not sufficient_data:
        return {
            "cv_accuracy": None, "cv_accuracy_std": None, "n_samples": n_samples,
            "n_classes": n_classes, "baseline_accuracy": baseline_accuracy,
            "sufficient_data": False,
        }

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    cv = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    scores = cross_val_score(clf, np.array(features), np.array(labels), cv=cv)

    return {
        "cv_accuracy": float(scores.mean()),
        "cv_accuracy_std": float(scores.std()),
        "n_samples": n_samples,
        "n_classes": n_classes,
        "baseline_accuracy": baseline_accuracy,
        "sufficient_data": True,
    }
