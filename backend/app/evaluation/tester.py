"""
Loads programming problems (with reference tests) that experiments are run
against.

Belongs to: backend/app/evaluation/
Phase: 6

See datasets/README.md for how to add HumanEval/MBPP once network access
to their hosting endpoints is available (not the case in this scaffold's
sandbox — see that README for the exact seam to extend).
"""
import json
from pathlib import Path

_DATASETS_DIR = Path(__file__).resolve().parents[3] / "datasets"


def load_problems(source: str = "custom") -> list[dict]:
    """Returns a list of problem dicts shaped like schemas.PromptCreate,
    ready to pass straight into ExperimentCreate.prompts.
    """
    if source == "custom":
        path = _DATASETS_DIR / "custom_problems.json"
        return json.loads(path.read_text())
    raise ValueError(
        f"Unknown dataset source: {source!r}. Only 'custom' is bundled; "
        "see datasets/README.md to add HumanEval/MBPP."
    )


def normalize_humaneval_test(assert_statements: str, entry_point: str) -> list[dict]:
    """Seam for Phase 6+ HumanEval integration: HumanEval ships tests as a
    block of `assert candidate(...) == ...` statements referencing a
    `candidate` function, not our {call, expected_output} shape. Not
    implemented here (no network access to fetch HumanEval to validate
    against) — documented so a future contributor has the exact
    conversion to write instead of guessing at the format.
    """
    raise NotImplementedError(
        "HumanEval test normalization is a documented extension point, not yet implemented "
        "— see datasets/README.md."
    )
