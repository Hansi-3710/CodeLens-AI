from app.ml.statistics import correlation, describe


def test_describe_basic_stats():
    result = describe([1.0, 2.0, 3.0, 4.0, 5.0])
    assert result["mean"] == 3.0
    assert result["median"] == 3.0
    assert result["n"] == 5
    assert result["ci_95_low"] < 3.0 < result["ci_95_high"]


def test_describe_empty_list():
    result = describe([])
    assert result["mean"] is None
    assert result["n"] == 0


def test_describe_ignores_none_values():
    result = describe([1.0, None, 3.0, None, 5.0])
    assert result["n"] == 3
    assert result["mean"] == 3.0


def test_describe_single_value_has_zero_stdev():
    result = describe([7.0])
    assert result["stdev"] == 0.0
    assert result["ci_95_low"] == result["ci_95_high"] == 7.0


def test_correlation_perfect_positive():
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    result = correlation(x, y)
    assert result["pearson_r"] > 0.99
    assert result["spearman_r"] > 0.99


def test_correlation_monotonic_nonlinear_favors_spearman():
    # y = x^5 is monotonic but strongly nonlinear — Spearman (rank-based)
    # should read as a stronger relationship than Pearson (linear) here.
    x = [1, 2, 3, 4, 5]
    y = [v ** 5 for v in x]
    result = correlation(x, y)
    assert result["spearman_r"] > 0.9999
    assert result["pearson_r"] < result["spearman_r"]


def test_correlation_insufficient_data_returns_none():
    result = correlation([1, 2], [1, 2])
    assert result["pearson_r"] is None
