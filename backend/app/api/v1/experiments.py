"""
Experiment lifecycle: create an experiment, kick off generation, fetch
aggregated results.

Belongs to: backend/app/api/v1/
Phase: 2 (CRUD — this file) / 4 (generate) / 6 (results)
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.analysis.complexity import analyze_complexity
from app.analysis.style_checker import analyze_style
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.database import crud, schemas
from app.database import session as db_session_module
from app.database.models import User
from app.database.session import get_db
from app.evaluation.metrics import build_model_comparison
from app.llm.base_provider import GenerationResult
from app.llm.llm_manager import LLMManager, ProviderError, build_provider

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[schemas.ExperimentRead])
def list_experiments(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    limit = min(limit, 100)  # hard ceiling: prevents an unbounded ?limit=999999 from forcing a full table scan
    return crud.list_experiments_for_owner(db, current_user.id, skip=skip, limit=limit)


@router.post("", response_model=schemas.ExperimentRead, status_code=201)
def create_experiment(
    payload: schemas.ExperimentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate requested models are registered before creating anything.
    for model_name in payload.models:
        if crud.get_model_by_name(db, model_name) is None:
            raise HTTPException(status_code=422, detail=f"Unknown model: {model_name}")

    experiment = crud.create_experiment(
        db,
        owner_id=current_user.id,
        name=payload.name,
        description=payload.description,
        prompts=[p.model_dump() for p in payload.prompts],
        selected_models=payload.models,
    )
    return experiment


@router.get("/{experiment_id}", response_model=schemas.ExperimentRead)
def get_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    experiment = crud.get_experiment(db, experiment_id)
    if experiment is None or experiment.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


async def _run_generation_job(experiment_id: str, temperature: float, max_tokens: int) -> None:
    """The actual generation work, run via FastAPI's BackgroundTasks after
    the HTTP response has already been sent.

    Opens its own DB session rather than reusing the request-scoped one
    from Depends(get_db) — that session is closed the moment the response
    is returned (see database/session.py's get_db), which is *before* this
    function runs. Reusing a closed session here would raise on first use;
    a background job owning its own session for its own lifetime is the
    correct pattern, not a workaround. Uses db_session_module.SessionLocal
    (module-qualified) rather than a direct import so tests can redirect it
    to the test database — see tests/conftest.py's `client` fixture.
    """
    db = db_session_module.SessionLocal()
    try:
        experiment = crud.get_experiment(db, experiment_id)
        if experiment is None:
            return  # deleted between the request and this running; nothing to do

        try:
            registered_models = crud.list_models(db, active_only=True)
            selected = set(experiment.selected_models or [])
            providers = {
                m.name: build_provider(m.name, m.provider, m.version)
                for m in registered_models
                if m.name in selected
            }
            manager = LLMManager(providers)

            for prompt in experiment.prompts:
                results = await manager.generate_all(
                    prompt.problem_statement,
                    model_names=list(providers.keys()),
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                for result in results:
                    if isinstance(result, GenerationResult):
                        model_row = crud.get_model_by_name(db, result.model_name)
                        solution = crud.save_generated_solution(
                            db,
                            prompt_id=prompt.id,
                            model_id=model_row.id,
                            code=result.code,
                            raw_response=result.raw_response,
                            temperature=result.temperature,
                            max_tokens=result.max_tokens,
                            tokens_used=result.tokens_used,
                            latency_seconds=result.latency_seconds,
                        )
                        # Static analysis is fast and in-process (unlike sandbox
                        # execution, which stays an explicit /execute call) so
                        # it runs eagerly here. A malformed solution (fails to
                        # parse) still produces a row — see complexity.py's
                        # parse_error handling — it just never crashes generation.
                        try:
                            complexity = analyze_complexity(result.code)
                            style = analyze_style(result.code)
                            crud.save_analysis_result(
                                db,
                                solution_id=solution.id,
                                lines_of_code=complexity["lines_of_code"],
                                cyclomatic_complexity=complexity["cyclomatic_complexity"],
                                big_o_estimate=complexity["big_o_estimate"],
                                maintainability_index=complexity["maintainability_index"],
                                style_score=style["style_score"],
                                pep8_violations=style["pep8_violations"],
                                docstring_coverage=style["docstring_coverage"],
                            )
                        except Exception as exc:  # noqa: BLE001 - analysis failure must not fail generation
                            logger.warning("Static analysis failed for solution %s: %s", solution.id, exc)
                    elif isinstance(result, ProviderError):
                        # A failed model doesn't fail the experiment — it just
                        # has no solution row for this prompt, visible in results
                        # as a gap rather than crashing the whole run.
                        pass
            crud.update_experiment_status(db, experiment_id, "completed")
        except Exception:
            logger.exception("Generation job failed for experiment %s", experiment_id)
            crud.update_experiment_status(db, experiment_id, "failed")
    finally:
        db.close()


@router.delete("/{experiment_id}", status_code=204)
def delete_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    experiment = crud.get_experiment(db, experiment_id)
    if experiment is None or experiment.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    crud.delete_experiment(db, experiment_id)


@router.post("/{experiment_id}/generate", response_model=schemas.GenerateResponse)
@limiter.limit("10/minute")
def generate_solutions(
    request: Request,
    experiment_id: str,
    background_tasks: BackgroundTasks,
    payload: schemas.GenerateRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validates synchronously (fast: ownership, prompts exist, models
    registered) then hands the actual generation off to a background task
    and returns immediately with status="running" — holding the HTTP
    connection open for however long N models x M prompts takes (easily
    tens of seconds to minutes) blocks a request-handling slot for no
    benefit, since the frontend already polls GET /experiments/{id} for
    status (see frontend/src/api/hooks.ts's useExperiment refetchInterval).
    """
    experiment = crud.get_experiment(db, experiment_id)
    if experiment is None or experiment.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if not experiment.prompts:
        raise HTTPException(status_code=422, detail="Experiment has no prompts")

    registered_models = crud.list_models(db, active_only=True)
    registered_names = {m.name for m in registered_models}
    missing = set(experiment.selected_models or []) - registered_names
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Selected model(s) no longer registered or active: {', '.join(sorted(missing))}",
        )
    if not experiment.selected_models:
        raise HTTPException(status_code=422, detail="Experiment has no selected models")

    temperature = payload.temperature if payload else 0.2
    max_tokens = payload.max_tokens if payload else 1024

    crud.update_experiment_status(db, experiment_id, "running")
    background_tasks.add_task(_run_generation_job, experiment_id, temperature, max_tokens)

    return {"experiment_id": experiment_id, "status": "running"}


@router.get("/{experiment_id}/solutions", response_model=list[schemas.SolutionSummary])
def list_solutions(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    experiment = crud.get_experiment(db, experiment_id)
    if experiment is None or experiment.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    solutions = crud.list_solutions_for_experiment(db, experiment_id)
    return [
        {
            "id": s.id,
            "prompt_id": s.prompt_id,
            "problem_statement": s.prompt.problem_statement,
            "model_name": s.model.name,
            "code": s.code,
        }
        for s in solutions
    ]


@router.get("/{experiment_id}/results", response_model=schemas.ExperimentResultsResponse)
def get_results(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    experiment = crud.get_experiment(db, experiment_id)
    if experiment is None or experiment.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Experiment not found")

    solutions = crud.list_solutions_for_experiment(db, experiment_id)
    return {
        "experiment_id": experiment_id,
        "status": experiment.status,
        "models": build_model_comparison(solutions),
    }
