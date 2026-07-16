from app.ml.classification import train_model_fingerprint_classifier


def test_insufficient_data_reported_not_crashed():
    result = train_model_fingerprint_classifier(features=[[1, 2]], labels=["gpt-4"])
    assert result["sufficient_data"] is False
    assert result["cv_accuracy"] is None


def test_perfectly_separable_classes_score_high():
    # Two clearly separated clusters, one per label — classifier should
    # comfortably beat the 50% majority-class baseline.
    features = [[0, 0], [0.1, 0.1], [0.05, 0], [10, 10], [10.1, 10.1], [10, 10.2]]
    labels = ["gpt-4", "gpt-4", "gpt-4", "llama-3-70b", "llama-3-70b", "llama-3-70b"]
    result = train_model_fingerprint_classifier(features, labels)
    assert result["sufficient_data"] is True
    assert result["cv_accuracy"] > result["baseline_accuracy"]


def test_single_class_is_insufficient_data():
    result = train_model_fingerprint_classifier([[1], [2], [3]], ["gpt-4", "gpt-4", "gpt-4"])
    assert result["sufficient_data"] is False
