from app.analysis.style_checker import analyze_style


def test_clean_documented_code_scores_high():
    code = '''def add(a, b):
    """Add two numbers."""
    return a + b
'''
    result = analyze_style(code)
    assert result["docstring_coverage"] == 1.0
    assert result["style_score"] > 0.8


def test_undocumented_function_lowers_docstring_coverage():
    code = "def add(a, b):\n    return a + b\n"
    result = analyze_style(code)
    assert result["docstring_coverage"] == 0.0


def test_code_with_no_functions_has_full_docstring_coverage():
    result = analyze_style("x = 1 + 1\n")
    assert result["docstring_coverage"] == 1.0
