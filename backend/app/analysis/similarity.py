"""
Pairwise similarity between two solutions via three methods: token
similarity, AST similarity, and embedding cosine similarity.

Belongs to: backend/app/analysis/
Phase: 6 (ML & Code Analysis)
"""
import difflib
import re

from app.analysis.ast_analyzer import analyze as ast_analyze

_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _normalize_tokens(code: str) -> str:
    """Strips comments/blank lines and collapses whitespace so two
    solutions that differ only in formatting score as identical on the
    token metric — token similarity should measure *content*, not style
    (style is style_checker.py's job)."""
    lines = [line.split("#", 1)[0].rstrip() for line in code.splitlines()]
    return "\n".join(line for line in lines if line.strip())


def token_similarity(code_a: str, code_b: str) -> float:
    """difflib ratio on normalized source — catches near-duplicate code,
    including copy-pasted solutions with only variable renames."""
    return difflib.SequenceMatcher(
        None, _normalize_tokens(code_a), _normalize_tokens(code_b)
    ).ratio()


def ast_similarity(code_a: str, code_b: str) -> float:
    """Compares node-type histograms (a cheap proxy for tree-edit distance)
    — catches structurally-equivalent code with different variable names,
    which token_similarity would score lower on."""
    summary_a = ast_analyze(code_a)
    summary_b = ast_analyze(code_b)
    if summary_a["parse_error"] or summary_b["parse_error"]:
        return 0.0

    counts_a, counts_b = summary_a["node_counts"], summary_b["node_counts"]
    all_node_types = set(counts_a) | set(counts_b)
    if not all_node_types:
        return 1.0

    # Cosine similarity over the node-type count vectors.
    dot = sum(counts_a.get(t, 0) * counts_b.get(t, 0) for t in all_node_types)
    norm_a = sum(v * v for v in counts_a.values()) ** 0.5
    norm_b = sum(v * v for v in counts_b.values()) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return min(1.0, max(0.0, dot / (norm_a * norm_b)))


def embedding_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """Cosine similarity between two precomputed embeddings (see ml/embeddings.py).
    Catches semantically similar solutions that look nothing alike
    token-for-token (e.g. iterative vs. recursive implementations of the
    same algorithm)."""
    dot = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = sum(a * a for a in vector_a) ** 0.5
    norm_b = sum(b * b for b in vector_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return min(1.0, max(-1.0, dot / (norm_a * norm_b)))


def compute_all_similarities(
    code_a: str, code_b: str, vector_a: list[float] | None = None, vector_b: list[float] | None = None
) -> dict:
    result = {
        "token_similarity": token_similarity(code_a, code_b),
        "ast_similarity": ast_similarity(code_a, code_b),
    }
    if vector_a is not None and vector_b is not None:
        result["embedding_similarity"] = embedding_similarity(vector_a, vector_b)
    else:
        result["embedding_similarity"] = None
    return result
