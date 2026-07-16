"""
Clusters solution embeddings to answer: "do models form distinct families
of solutions?" Also produces 2D projections (PCA and UMAP) for the
Diversity Map.

Belongs to: backend/app/ml/
Phase: 6 (ML & Code Analysis)
"""
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from sklearn.decomposition import PCA


def kmeans_cluster(vectors: list[list[float]], n_clusters: int = 3) -> list[int]:
    """Returns a cluster label per vector. n_clusters is capped at the
    number of samples so this never raises on small experiments (e.g. a
    3-model, 1-prompt run has only 3 points to cluster)."""
    if len(vectors) < 2:
        return [0] * len(vectors)
    k = min(n_clusters, len(vectors))
    labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(np.array(vectors))
    return labels.tolist()


def dbscan_cluster(vectors: list[list[float]], eps: float = 0.5, min_samples: int = 2) -> list[int]:
    """DBSCAN labels: -1 means "noise" (didn't fit any cluster) — useful
    for flagging a model's solution as a genuine outlier rather than
    forcing it into the nearest group, which KMeans always does."""
    if len(vectors) < min_samples:
        return [-1] * len(vectors)
    labels = DBSCAN(eps=eps, min_samples=min_samples, metric="cosine").fit_predict(np.array(vectors))
    return labels.tolist()


def project_2d_pca(vectors: list[list[float]]) -> list[list[float]]:
    """PCA projection to 2D: linear and fully deterministic (no
    random_state sensitivity, no minimum-sample requirement beyond 2
    points), unlike UMAP's nonlinear, stochastic embedding. Useful as a
    fast sanity check against project_2d()'s UMAP output, and as the only
    option that works meaningfully on very small experiments where UMAP's
    neighbor graph is barely defined.
    """
    arr = np.array(vectors)
    if len(vectors) < 2:
        return [[0.0, 0.0] for _ in vectors]
    n_components = min(2, arr.shape[0], arr.shape[1])
    reduced = PCA(n_components=n_components, random_state=42).fit_transform(arr)
    if n_components == 1:
        # A single point (or a degenerate 1D embedding space) still needs
        # a 2D coordinate for the frontend scatter plot.
        return [[float(row[0]), 0.0] for row in reduced]
    return reduced.tolist()


def project_2d(vectors: list[list[float]], method: str = "umap") -> list[list[float]]:
    """UMAP projection to 2D for the frontend's Diversity Map scatter plot
    (method="pca" delegates to project_2d_pca instead — see its docstring
    for when that's the better choice). UMAP needs more neighbors than
    points available in tiny experiments, so n_neighbors is capped below
    len(vectors).
    """
    if method == "pca":
        return project_2d_pca(vectors)

    if len(vectors) < 3:
        # UMAP is undefined below ~3 points; fall back to a trivial
        # deterministic layout so the frontend always has coordinates to plot.
        return [[float(i), 0.0] for i in range(len(vectors))]

    import umap  # imported lazily: heavy dependency, only needed here

    n_neighbors = min(15, len(vectors) - 1)
    reducer = umap.UMAP(n_components=2, n_neighbors=n_neighbors, random_state=42)
    projected = reducer.fit_transform(np.array(vectors))
    return projected.tolist()
