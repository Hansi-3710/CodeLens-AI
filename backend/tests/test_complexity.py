from app.analysis.complexity import analyze_complexity, estimate_big_o
from app.analysis.ast_analyzer import analyze as ast_analyze


def test_constant_time_function():
    result = analyze_complexity("def add(a, b):\n    return a + b\n")
    assert result["big_o_estimate"] == "O(1)"
    assert result["cyclomatic_complexity"] is not None


def test_single_loop_is_linear():
    code = "def total(nums):\n    s = 0\n    for n in nums:\n        s += n\n    return s\n"
    assert analyze_complexity(code)["big_o_estimate"] == "O(n)"


def test_naive_recursive_fibonacci_is_exponential():
    code = "def fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n"
    assert analyze_complexity(code)["big_o_estimate"] == "O(2^n)"


def test_syntax_error_does_not_crash_complexity_analysis():
    result = analyze_complexity("def broken(:\n    pass")
    assert result["big_o_estimate"] == "unknown"
    assert result["cyclomatic_complexity"] is None
