"""
Statistical comparison across models: mean/median/stdev/confidence
intervals per metric, and correlation analysis (e.g. code length vs
pass rate).

Belongs to: backend/app/ml/
Phase: 6 (ML & Code Analysis)
"""
import numpy as np
from scipy import stats


def describe(values: list[float]) -> dict:
    """Returns mean/median/stdev/95% CI for a list of metric values (e.g.
    one model's pass rates across all prompts in an experiment).

    Uses a t-distribution CI (appropriate for the small sample sizes
    typical of a single experiment) rather than assuming normality holds
    at scale.
    """
    arr = np.array([v for v in values if v is not None], dtype=float)
    n = len(arr)
    if n == 0:
        return {"mean": None, "median": None, "stdev": None, "ci_95_low": None, "ci_95_high": None, "n": 0}
    if n == 1:
        return {"mean": float(arr[0]), "median": float(arr[0]), "stdev": 0.0,
                "ci_95_low": float(arr[0]), "ci_95_high": float(arr[0]), "n": 1}

    mean = float(np.mean(arr))
    median = float(np.median(arr))
    stdev = float(np.std(arr, ddof=1))
    sem = stdev / (n ** 0.5)
    margin = stats.t.ppf(0.975, df=n - 1) * sem
    return {
        "mean": mean, "median": median, "stdev": stdev,
        "ci_95_low": mean - margin, "ci_95_high": mean + margin, "n": n,
    }


def correlation(x: list[float], y: list[float]) -> dict:
    """Pearson AND Spearman correlation between two paired metrics (e.g.
    code length vs pass rate). Returns None values instead of raising when
    there isn't enough paired data (n < 3) to compute a meaningful
    correlation.

    Both are reported because they answer different questions: Pearson
    assumes a linear relationship, while Spearman (rank correlation) only
    assumes a monotonic one — a real "longer code -> lower pass rate"
    effect that saturates or has outliers can show a much weaker Pearson r
    than Spearman rho, and reporting only Pearson would understate it.
    """
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 3:
        return {"pearson_r": None, "pearson_p": None, "spearman_r": None, "spearman_p": None, "n": len(pairs)}

    xs, ys = zip(*pairs)
    pearson_r, pearson_p = stats.pearsonr(xs, ys)
    spearman_r, spearman_p = stats.spearmanr(xs, ys)
    return {
        "pearson_r": float(pearson_r), "pearson_p": float(pearson_p),
        "spearman_r": float(spearman_r), "spearman_p": float(spearman_p),
        "n": len(pairs),
    }
