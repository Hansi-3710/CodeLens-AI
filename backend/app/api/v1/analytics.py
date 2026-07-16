"""
Cross-model analytics for an experiment: similarity heatmap, cluster/
diversity map, statistical comparisons.

Belongs to: backend/app/api/v1/
Phase: 6 (ML & Code Analysis)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.analysis.similarity import compute_all_similarities
from app.core.security import get_current_user
from app.database import crud, schemas
from app.database.models import User
from app.database.session import get_db
from app.ml.classification import train_model_fingerprint_classifier
from app.ml.clustering import kmeans_cluster, project_2d
from app.ml.statistics import correlation, describe

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_owned_experiment(db: Session, experiment_id: str, current_user: User):
    experiment = crud.get_experiment(db, experiment_id)
    if experiment is None or experiment.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@router.get("/{experiment_id}", response_model=schemas.AnalyticsSummary)
def get_analytics(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_experiment(db, experiment_id, current_user)
    solutions = crud.list_solutions_for_experiment(db, experiment_id)

    lengths = [len(s.code.splitlines()) for s in solutions]
    pass_rates = [s.execution_result.pass_rate for s in solutions if s.execution_result]
    complexities = [
        s.analysis_result.cyclomatic_complexity for s in solutions
        if s.analysis_result and s.analysis_result.cyclomatic_complexity is not None
    ]

    length_vs_pass_rate = correlation(
        [len(s.code.splitlines()) for s in solutions if s.execution_result],
        [s.execution_result.pass_rate for s in solutions if s.execution_result],
    )

    return {
        "experiment_id": experiment_id,
        "n_solutions": len(solutions),
        "code_length": describe(lengths),
        "pass_rate": describe(pass_rates),
        "cyclomatic_complexity": describe(complexities),
        "correlations": {
            "code_length_vs_pass_rate": length_vs_pass_rate,
        },
        "model_fingerprint": train_model_fingerprint_classifier(
            features=[[len(s.code.splitlines()), (s.analysis_result.cyclomatic_complexity or 0)] for s in solutions],
            labels=[s.model.name for s in solutions],
        ) if solutions else {"sufficient_data": False},
    }


@router.get("/{experiment_id}/similarity", response_model=schemas.SimilarityMatrixResponse)
def get_similarity_matrix(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_owned_experiment(db, experiment_id, current_user)
    solutions = crud.list_solutions_for_experiment(db, experiment_id)

    # Similarity is only meaningful between solutions to the *same* prompt
    # (comparing a shortest-path solution to a palindrome-check solution
    # tells you nothing about model similarity) — group first.
    by_prompt: dict[str, list] = {}
    for s in solutions:
        by_prompt.setdefault(s.prompt_id, []).append(s)

    pairs = []
    for prompt_solutions in by_prompt.values():
        for i in range(len(prompt_solutions)):
            for j in range(i + 1, len(prompt_solutions)):
                a, b = prompt_solutions[i], prompt_solutions[j]
                scores = compute_all_similarities(a.code, b.code)
                pairs.append({
                    "prompt_id": a.prompt_id,
                    "model_a": a.model.name,
                    "model_b": b.model.name,
                    **scores,
                })

    return {"experiment_id": experiment_id, "pairs": pairs}


@router.get("/{experiment_id}/clusters", response_model=schemas.ClustersResponse)
def get_clusters(
    experiment_id: str,
    method: str = "umap",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if method not in ("umap", "pca"):
        raise HTTPException(status_code=422, detail="method must be 'umap' or 'pca'")

    _get_owned_experiment(db, experiment_id, current_user)
    solutions = crud.list_solutions_for_experiment(db, experiment_id)

    embedded = [s for s in solutions if s.embedding is not None]
    if not embedded:
        return {
            "experiment_id": experiment_id, "points": [], "method": method,
            "note": "No embeddings available yet — embeddings are computed lazily and "
                    "require network access to download the embedding model (see "
                    "app/ml/embeddings.py's docstring).",
        }

    vectors = [s.embedding.vector for s in embedded]
    coords = project_2d(vectors, method=method)
    labels = kmeans_cluster(vectors, n_clusters=min(3, len(vectors)))

    points = [
        {
            "solution_id": s.id, "model": s.model.name, "prompt_id": s.prompt_id,
            "x": coords[i][0], "y": coords[i][1], "cluster": labels[i],
        }
        for i, s in enumerate(embedded)
    ]
    return {"experiment_id": experiment_id, "points": points, "method": method}
