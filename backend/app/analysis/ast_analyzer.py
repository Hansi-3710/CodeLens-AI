"""
Parses Python source into an AST and produces a structured, comparable
summary (node-type histogram + tree shape/depth) used by both the quality
analyzer and the similarity engine.

Belongs to: backend/app/analysis/
Phase: 6 (ML & Code Analysis)
"""
import ast
from collections import Counter


class _DepthVisitor(ast.NodeVisitor):
    """Walks the tree tracking max nesting depth and a node-type histogram
    in one pass, since both are cheap to compute together."""

    def __init__(self):
        self.node_counts: Counter[str] = Counter()
        self.max_depth = 0
        self._current_depth = 0

    def generic_visit(self, node):
        self.node_counts[type(node).__name__] += 1
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
        super().generic_visit(node)
        self._current_depth -= 1


class _LoopNestingVisitor(ast.NodeVisitor):
    """Tracks max *loop* nesting depth specifically — general AST depth
    (from _DepthVisitor above) includes expression-level nodes (BinOp,
    Load/Store contexts, etc.) and is not a usable proxy for "how many
    loops are nested," which is what the Big-O heuristic actually needs.
    """

    def __init__(self):
        self.max_depth = 0
        self._current = 0

    def _visit_loop(self, node):
        self._current += 1
        self.max_depth = max(self.max_depth, self._current)
        self.generic_visit(node)
        self._current -= 1

    def visit_For(self, node):
        self._visit_loop(node)

    def visit_While(self, node):
        self._visit_loop(node)


def analyze(code: str) -> dict:
    """Returns {"node_counts": {...}, "max_depth": int, "function_count": int,
    "loop_count": int, "loop_nesting_depth": int, "branch_count": int,
    "recursion_detected": bool, "parse_error": str | None}.

    A parse error (invalid Python) is reported, not raised — a solution
    that fails to parse is itself a meaningful analysis result, not a
    pipeline crash.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return {
            "node_counts": {}, "max_depth": 0, "function_count": 0,
            "loop_count": 0, "loop_nesting_depth": 0, "branch_count": 0,
            "recursion_detected": False, "parse_error": str(exc),
        }

    visitor = _DepthVisitor()
    visitor.visit(tree)

    loop_visitor = _LoopNestingVisitor()
    loop_visitor.visit(tree)

    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    recursion_detected = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in function_names
        for node in ast.walk(tree)
    )

    return {
        "node_counts": dict(visitor.node_counts),
        "max_depth": visitor.max_depth,
        "function_count": sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))),
        "loop_count": sum(1 for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While))),
        "loop_nesting_depth": loop_visitor.max_depth,
        "branch_count": sum(1 for n in ast.walk(tree) if isinstance(n, ast.If)),
        "recursion_detected": recursion_detected,
        "parse_error": None,
    }
