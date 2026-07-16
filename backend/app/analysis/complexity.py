"""
Computes cyclomatic complexity, maintainability index, and a heuristic
Big-O estimate for a generated solution.

Belongs to: backend/app/analysis/
Phase: 6 (ML & Code Analysis)
Library: radon
"""
from radon.complexity import cc_visit
from radon.metrics import mi_visit

from app.analysis.ast_analyzer import analyze as ast_analyze


def estimate_big_o(ast_summary: dict) -> str:
    """Heuristic, not a proof: derives a rough complexity class from loop
    nesting depth and recursion. Always presented to the user as an
    *estimate* (see ARCHITECTURE.md's design-decisions section) — static
    analysis cannot determine true asymptotic complexity in general.
    """
    if ast_summary.get("parse_error"):
        return "unknown"

    loops = ast_summary.get("loop_count", 0)
    recursive = ast_summary.get("recursion_detected", False)
    nesting = ast_summary.get("loop_nesting_depth", 0)

    if recursive and loops == 0:
        return "O(2^n)"  # naive recursion without memoization, common LLM output
    if recursive:
        return "O(n log n)"  # recursive + iterative hybrid (e.g. divide and conquer)
    if loops == 0:
        return "O(1)"
    if nesting >= 3:
        return "O(n^3)"
    if nesting == 2:
        return "O(n^2)"
    return "O(n)"


def analyze_complexity(code: str) -> dict:
    """Returns {"cyclomatic_complexity": float, "maintainability_index": float,
    "big_o_estimate": str, "lines_of_code": int}."""
    lines_of_code = len([line for line in code.splitlines() if line.strip()])

    try:
        blocks = cc_visit(code)
        avg_complexity = (sum(b.complexity for b in blocks) / len(blocks)) if blocks else 1.0
    except SyntaxError:
        avg_complexity = None

    try:
        maintainability = mi_visit(code, multi=True)
    except SyntaxError:
        maintainability = None

    ast_summary = ast_analyze(code)

    return {
        "cyclomatic_complexity": avg_complexity,
        "maintainability_index": maintainability,
        "big_o_estimate": estimate_big_o(ast_summary),
        "lines_of_code": lines_of_code,
    }
