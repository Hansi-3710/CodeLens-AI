from app.analysis.ast_analyzer import analyze


def test_detects_recursion():
    code = "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n"
    result = analyze(code)
    assert result["recursion_detected"] is True
    assert result["function_count"] == 1
    assert result["branch_count"] == 1


def test_detects_loops_and_no_recursion():
    code = "def total(nums):\n    s = 0\n    for n in nums:\n        s += n\n    return s\n"
    result = analyze(code)
    assert result["loop_count"] == 1
    assert result["recursion_detected"] is False


def test_syntax_error_reported_not_raised():
    result = analyze("def broken(:\n    pass")
    assert result["parse_error"] is not None
    assert result["function_count"] == 0


def test_nested_loops_increase_depth():
    shallow = analyze("def f(a):\n    for x in a:\n        pass\n")
    deep = analyze("def f(a):\n    for x in a:\n        for y in x:\n            pass\n")
    assert deep["max_depth"] > shallow["max_depth"]
