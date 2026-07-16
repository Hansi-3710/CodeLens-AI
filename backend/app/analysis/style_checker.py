"""
Runs static style/lint checks and computes a documentation coverage score.

Belongs to: backend/app/analysis/
Phase: 6 (ML & Code Analysis)
Tools: flake8 (pylint omitted from the default path — much slower per-call
and largely overlapping with flake8 for single-file style checks; kept as
a documented extension point below).
"""
import ast
import subprocess
import sys
import tempfile
from pathlib import Path


def _run_flake8(code: str) -> list[str]:
    """Runs flake8 against `code` in a throwaway temp file. This is STATIC
    analysis only — flake8 parses and inspects the file, it never executes
    it — so this is safe to run in-process, unlike the sandbox in
    execution/, which is reserved for actually running the code.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", "--max-line-length=100", temp_path],
            capture_output=True, text=True, timeout=10,
        )
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        # Strip the temp path prefix so violations don't leak the sandbox filesystem layout.
        return [line.split(":", 1)[1] if ":" in line else line for line in lines]
    finally:
        Path(temp_path).unlink(missing_ok=True)


def _docstring_coverage(code: str) -> float:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0.0

    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not functions:
        return 1.0  # no functions to document is vacuously "fully documented"
    documented = sum(1 for fn in functions if ast.get_docstring(fn))
    return documented / len(functions)


def analyze_style(code: str) -> dict:
    """Returns {"pep8_violations": int, "docstring_coverage": float,
    "style_score": float}. style_score is a simple 0-1 composite:
    fewer violations per line + higher docstring coverage = higher score.
    """
    violations = _run_flake8(code)
    lines_of_code = max(len([line for line in code.splitlines() if line.strip()]), 1)
    violation_density = len(violations) / lines_of_code
    docstring_coverage = _docstring_coverage(code)

    # Composite: violation density dominates (capped so one bad line
    # doesn't zero out the score), docstring coverage contributes up to 30%.
    style_score = max(0.0, 1.0 - min(violation_density, 0.7)) * 0.7 + docstring_coverage * 0.3

    return {
        "pep8_violations": len(violations),
        "docstring_coverage": docstring_coverage,
        "style_score": round(style_score, 4),
    }
