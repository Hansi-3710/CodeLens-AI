# Datasets

`custom_problems.json` — a small hand-written problem set (5 problems) used
as the default when no external dataset is configured. Loaded by
`backend/app/evaluation/tester.py`.

## HumanEval / MBPP

The platform is designed to support these standard benchmarks
(`Prompt.source_dataset` accepts `"HumanEval"` / `"MBPP"` / `"custom"`), but
downloading and normalizing them isn't done in this scaffold — both are
distributed via HTTPS/HuggingFace endpoints not reachable from this
sandbox's restricted network egress. To add them in a real deployment:

1. Download `HumanEval.jsonl.gz` from the openai/human-eval GitHub repo, or
   load `mbpp` via `datasets.load_dataset("mbpp")`.
2. Normalize each problem into the same shape as `custom_problems.json`:
   `{problem_statement, language, difficulty, source_dataset, reference_tests}`.
   HumanEval/MBPP tests are `assert`-statement based rather than
   `{call, expected_output}` pairs — `evaluation/tester.py`'s loader has a
   documented seam (`normalize_humaneval_test`) for that conversion.
3. Save as a `.json` file in this directory and point `tester.load_problems()`
   at it.
