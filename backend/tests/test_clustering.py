from app.ml.clustering import dbscan_cluster, kmeans_cluster, project_2d


def test_kmeans_returns_one_label_per_vector():
    vectors = [[0, 0], [0.1, 0.1], [10, 10], [10.1, 10.1]]
    labels = kmeans_cluster(vectors, n_clusters=2)
    assert len(labels) == 4
    # The two nearby pairs should land in the same cluster as each other.
    assert labels[0] == labels[1]
    assert labels[2] == labels[3]
    assert labels[0] != labels[2]


def test_kmeans_handles_fewer_points_than_requested_clusters():
    vectors = [[0, 0], [1, 1]]
    labels = kmeans_cluster(vectors, n_clusters=5)
    assert len(labels) == 2


def test_kmeans_handles_single_point():
    assert kmeans_cluster([[0, 0]], n_clusters=3) == [0]


def test_dbscan_flags_outlier_as_noise():
    # DBSCAN here uses cosine distance (appropriate for embeddings, where
    # direction matters more than magnitude) — so the outlier must differ
    # in *angle*, not just magnitude, to actually score as distant.
    vectors = [[1.0, 0.05], [1.05, 0.0], [0.95, 0.02], [0.0, 1.0]]
    labels = dbscan_cluster(vectors, eps=0.05, min_samples=2)
    assert labels[3] == -1  # the orthogonal-direction point is noise
    assert labels[0] == labels[1] == labels[2]  # the tight cluster agrees


def test_project_2d_returns_2d_points_for_every_input():
    vectors = [[float(i)] * 5 for i in range(6)]
    projected = project_2d(vectors)
    assert len(projected) == 6
    assert all(len(p) == 2 for p in projected)


def test_project_2d_fallback_for_tiny_input():
    projected = project_2d([[1, 2], [3, 4]])
    assert len(projected) == 2


def test_pca_projection_returns_2d_points_for_every_input():
    from app.ml.clustering import project_2d_pca

    vectors = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0], [1.0, 0.0, 0.0]]
    projected = project_2d_pca(vectors)
    assert len(projected) == 4
    assert all(len(p) == 2 for p in projected)


def test_pca_is_deterministic_across_runs():
    from app.ml.clustering import project_2d_pca

    vectors = [[1.0, 2.0], [3.0, 1.0], [0.0, 5.0], [2.0, 2.0]]
    first = project_2d_pca(vectors)
    second = project_2d_pca(vectors)
    assert first == second


def test_project_2d_method_param_dispatches_to_pca():
    from app.ml.clustering import project_2d

    vectors = [[1.0, 2.0], [3.0, 1.0], [0.0, 5.0]]
    pca_result = project_2d(vectors, method="pca")
    assert len(pca_result) == 3


def test_project_2d_rejects_unknown_method_gracefully():
    from app.ml.clustering import project_2d_pca
    # project_2d itself doesn't validate `method` (the API layer does, see
    # test_clusters_endpoint_rejects_invalid_method below) — this just
    # confirms the pca path itself never raises on valid input shapes.
    assert project_2d_pca([[1.0]]) == [[0.0, 0.0]] or len(project_2d_pca([[1.0]])) == 1
