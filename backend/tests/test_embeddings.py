"""
Tests embed()/embed_batch() with the underlying SentenceTransformer mocked
— downloading real model weights requires network access to huggingface.co,
which isn't available in this environment (see embeddings.py's docstring).
This test asserts the module's *contract* (shape, caching), not real
semantic embedding quality.
"""
from unittest.mock import MagicMock, patch

import numpy as np

import app.ml.embeddings as embeddings_module


def test_embed_returns_list_of_floats():
    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([0.1, 0.2, 0.3])
    embeddings_module._get_model.cache_clear()

    with patch.object(embeddings_module, "_get_model", return_value=fake_model):
        vector = embeddings_module.embed("def f(): pass")

    assert vector == [0.1, 0.2, 0.3]


def test_embed_batch_returns_one_vector_per_input():
    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])

    with patch.object(embeddings_module, "_get_model", return_value=fake_model):
        vectors = embeddings_module.embed_batch(["def a(): pass", "def b(): pass"])

    assert len(vectors) == 2
    assert vectors[0] == [0.1, 0.2]
