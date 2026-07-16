from app.analysis.similarity import ast_similarity, token_similarity, embedding_similarity, compute_all_similarities


def test_identical_code_has_similarity_one():
    code = "def add(a, b):\n    return a + b\n"
    assert token_similarity(code, code) == 1.0
    assert ast_similarity(code, code) == 1.0


def test_renamed_variables_score_high_on_ast_low_on_token():
    code_a = "def add(a, b):\n    return a + b\n"
    code_b = "def sum_two(x, y):\n    return x + y\n"
    # Structurally identical (same AST shape) despite different names/formatting.
    assert ast_similarity(code_a, code_b) > 0.9
    # Token-level, the renamed identifiers pull the ratio down noticeably
    # relative to the identical-code case above.
    assert token_similarity(code_a, code_b) < 1.0


def test_different_algorithms_score_lower_on_ast():
    iterative = "def total(nums):\n    s = 0\n    for n in nums:\n        s += n\n    return s\n"
    recursive = "def total(nums):\n    if not nums:\n        return 0\n    return nums[0] + total(nums[1:])\n"
    assert ast_similarity(iterative, recursive) < 1.0


def test_embedding_similarity_cosine():
    assert embedding_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert embedding_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_compute_all_similarities_without_embeddings():
    code = "def f(): pass"
    result = compute_all_similarities(code, code)
    assert result["embedding_similarity"] is None
    assert result["token_similarity"] == 1.0
