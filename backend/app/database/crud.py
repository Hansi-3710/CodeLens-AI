"""
Data-access layer — all raw SQLAlchemy queries live here so API routers
stay thin and testable with mocked CRUD functions.

Belongs to: backend/app/database/
Phase: 2/3 (Backend Foundation / Database)
"""
from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.database import models


# ---- Users -----------------------------------------------------------------

def create_user(db: Session, email: str, password: str, full_name: str | None = None) -> models.User:
    from app.core.security import hash_password  # local import: avoids a security<->crud circular import

    user = models.User(email=email, hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: str) -> models.User | None:
    return db.get(models.User, user_id)


def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()


# ---- AI Models ---------------------------------------------------------------

def create_model(
    db: Session, name: str, provider: str, version: str | None = None, context_window: int | None = None
) -> models.AIModel:
    existing = db.query(models.AIModel).filter(models.AIModel.name == name).first()
    if existing:
        return existing
    model = models.AIModel(name=name, provider=provider, version=version, context_window=context_window)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def list_models(db: Session, active_only: bool = True, skip: int = 0, limit: int = 50) -> list[models.AIModel]:
    query = db.query(models.AIModel)
    if active_only:
        query = query.filter(models.AIModel.is_active.is_(True))
    return query.order_by(models.AIModel.name).offset(skip).limit(limit).all()


def get_model_by_name(db: Session, name: str) -> models.AIModel | None:
    return db.query(models.AIModel).filter(models.AIModel.name == name).first()


# ---- Experiments ---------------------------------------------------------------

def create_experiment(
    db: Session,
    owner_id: str,
    name: str,
    description: str | None,
    prompts: list[dict],
    selected_models: list[str],
) -> models.Experiment:
    experiment = models.Experiment(
        owner_id=owner_id, name=name, description=description, status="pending",
        selected_models=selected_models,
    )
    db.add(experiment)
    db.flush()  # get experiment.id before creating child rows

    for p in prompts:
        prompt = models.Prompt(
            experiment_id=experiment.id,
            problem_statement=p["problem_statement"],
            language=p.get("language", "python"),
            difficulty=p.get("difficulty"),
            reference_tests=p.get("reference_tests"),
            source_dataset=p.get("source_dataset"),
        )
        db.add(prompt)

    db.commit()
    db.refresh(experiment)
    return experiment


def get_experiment(db: Session, experiment_id: str) -> models.Experiment | None:
    return db.get(models.Experiment, experiment_id)


def list_experiments_for_owner(
    db: Session, owner_id: str, skip: int = 0, limit: int = 50
) -> list[models.Experiment]:
    return (
        db.query(models.Experiment)
        .filter(models.Experiment.owner_id == owner_id)
        .order_by(models.Experiment.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_experiment(db: Session, experiment_id: str) -> None:
    experiment = db.get(models.Experiment, experiment_id)
    if experiment is not None:
        db.delete(experiment)  # cascades to prompts -> solutions -> execution/analysis/embedding, see models.py
        db.commit()


def update_experiment_status(db: Session, experiment_id: str, status: str) -> models.Experiment | None:
    experiment = db.get(models.Experiment, experiment_id)
    if experiment is None:
        return None
    experiment.status = status
    if status in ("completed", "failed"):
        from datetime import datetime, timezone
        experiment.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(experiment)
    return experiment


# ---- Generated Solutions ---------------------------------------------------------------

def save_generated_solution(
    db: Session,
    prompt_id: str,
    model_id: str,
    code: str,
    raw_response: str,
    temperature: float,
    max_tokens: int,
    tokens_used: int,
    latency_seconds: float,
) -> models.GeneratedSolution:
    solution = models.GeneratedSolution(
        prompt_id=prompt_id,
        model_id=model_id,
        code=code,
        raw_response=raw_response,
        temperature=temperature,
        max_tokens=max_tokens,
        tokens_used=tokens_used,
        generation_latency_seconds=latency_seconds,
    )
    db.add(solution)
    db.commit()
    db.refresh(solution)
    return solution


def list_solutions_for_experiment(db: Session, experiment_id: str) -> list[models.GeneratedSolution]:
    """Eager-loads every relationship its callers touch (evaluation/metrics.py's
    build_model_comparison, analytics.py's stats/similarity/clusters endpoints,
    and the /experiments/{id}/solutions endpoint all access
    .model, .prompt, .execution_result, .analysis_result, .embedding on
    every row) — without this, each of those is a separate lazy-load query
    per solution: an N+1 that turns "list solutions" into up to 5N+1 queries
    for an experiment with N solutions.
    """
    return (
        db.query(models.GeneratedSolution)
        .join(models.Prompt)
        .filter(models.Prompt.experiment_id == experiment_id)
        .options(
            joinedload(models.GeneratedSolution.model),
            joinedload(models.GeneratedSolution.prompt),
            joinedload(models.GeneratedSolution.execution_result),
            joinedload(models.GeneratedSolution.analysis_result),
            joinedload(models.GeneratedSolution.embedding),
        )
        .all()
    )


def get_solution(db: Session, solution_id: str) -> models.GeneratedSolution | None:
    return (
        db.query(models.GeneratedSolution)
        .options(
            joinedload(models.GeneratedSolution.model),
            joinedload(models.GeneratedSolution.prompt).joinedload(models.Prompt.experiment),
            joinedload(models.GeneratedSolution.execution_result),
            joinedload(models.GeneratedSolution.analysis_result),
        )
        .filter(models.GeneratedSolution.id == solution_id)
        .first()
    )


# ---- Execution / Analysis / Embeddings ---------------------------------------------------------------

def save_execution_result(db: Session, solution_id: str, **fields) -> models.ExecutionResult:
    result = models.ExecutionResult(solution_id=solution_id, **fields)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def save_analysis_result(db: Session, solution_id: str, **fields) -> models.AnalysisResult:
    result = models.AnalysisResult(solution_id=solution_id, **fields)
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def save_embedding(db: Session, solution_id: str, vector: list[float], model_name: str) -> models.Embedding:
    embedding = models.Embedding(solution_id=solution_id, vector=vector, model_name=model_name)
    db.add(embedding)
    db.commit()
    db.refresh(embedding)
    return embedding


def save_similarity_score(db: Session, solution_a_id: str, solution_b_id: str, **fields) -> models.SimilarityScore:
    score = models.SimilarityScore(solution_a_id=solution_a_id, solution_b_id=solution_b_id, **fields)
    db.add(score)
    db.commit()
    db.refresh(score)
    return score
