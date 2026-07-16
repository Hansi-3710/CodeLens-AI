"""
Aggregate evaluation metrics per model per experiment: pass rate, average
runtime, average memory, correctness confidence interval. This is the
module that produces the MODEL COMPARISON view.

Belongs to: backend/app/evaluation/
Phase: 6
"""
from app.database import models
from app.ml.statistics import describe


def build_model_comparison(solutions: list[models.GeneratedSolution]) -> list[dict]:
    """Groups solutions by model and computes the leaderboard row for each:
    correctness (mean pass rate + 95% CI), average runtime, and the most
    common Big-O estimate observed for that model on this experiment.
    """
    by_model: dict[str, list[models.GeneratedSolution]] = {}
    for solution in solutions:
        by_model.setdefault(solution.model.name, []).append(solution)

    rows = []
    for model_name, model_solutions in by_model.items():
        pass_rates = [s.execution_result.pass_rate for s in model_solutions if s.execution_result]
        runtimes = [s.execution_result.runtime_seconds for s in model_solutions if s.execution_result]
        complexities = [
            s.analysis_result.big_o_estimate for s in model_solutions
            if s.analysis_result and s.analysis_result.big_o_estimate
        ]
        most_common_complexity = max(set(complexities), key=complexities.count) if complexities else None

        correctness_stats = describe(pass_rates)
        runtime_stats = describe(runtimes)

        rows.append({
            "model": model_name,
            "correctness": correctness_stats["mean"],
            "correctness_ci_95": [correctness_stats["ci_95_low"], correctness_stats["ci_95_high"]],
            "avg_runtime_s": runtime_stats["mean"],
            "complexity": most_common_complexity,
            "n_solutions": len(model_solutions),
        })

    rows.sort(key=lambda r: (r["correctness"] if r["correctness"] is not None else -1), reverse=True)
    return rows
