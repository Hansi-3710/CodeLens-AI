"""
Converts source code into a dense vector using Sentence Transformers,
so solutions can be compared, clustered, and visualized.

Belongs to: backend/app/ml/
Phase: 6 (ML & Code Analysis)

Note: sentence-transformers downloads model weights from huggingface.co on
first use. In network-restricted environments (e.g. this scaffold's CI
sandbox, which only allows pypi/npm/github egress — see the deployment
README) that download will fail. embed() surfaces that failure clearly
rather than silently returning garbage; get_embedder() is the one seam to
swap in a self-hosted model mirror in production if needed.
"""
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_model():
    """Loads the embedding model once per process. Lazy + cached so
    importing this module (e.g. for type checking or in tests that mock
    embed()) never pays the model-load cost."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed(code: str) -> list[float]:
    """Returns a 384-dim embedding vector for the given source code."""
    model = _get_model()
    vector = model.encode(code, convert_to_numpy=True)
    return vector.tolist()


def embed_batch(code_snippets: list[str]) -> list[list[float]]:
    """Batched embedding — one model forward pass instead of N, used when
    embedding every solution in an experiment at once."""
    model = _get_model()
    vectors = model.encode(code_snippets, convert_to_numpy=True)
    return vectors.tolist()
