"""
Individual solution operations: fetch a solution, run it through the
execution sandbox.

Belongs to: backend/app/api/v1/
Phase: 2 (CRUD) / 5 (execute)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import crud, schemas
from app.database.models import User
from app.database.session import get_db
from app.execution.sandbox_runner import run_solution_in_sandbox

router = APIRouter()


def _get_owned_solution(db: Session, solution_id: str, current_user: User):
    solution = crud.get_solution(db, solution_id)
    if solution is None or solution.prompt.experiment.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Solution not found")
    return solution


@router.get("/{solution_id}", response_model=schemas.SolutionRead)
def get_solution(
    solution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    solution = _get_owned_solution(db, solution_id, current_user)
    return {
        "id": solution.id,
        "model_name": solution.model.name,
        "code": solution.code,
        "pass_rate": solution.execution_result.pass_rate if solution.execution_result else None,
        "runtime_seconds": solution.execution_result.runtime_seconds if solution.execution_result else None,
        "cyclomatic_complexity": solution.analysis_result.cyclomatic_complexity if solution.analysis_result else None,
    }


@router.post("/{solution_id}/execute", response_model=schemas.ExecuteResponse)
def execute_solution(
    solution_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    solution = _get_owned_solution(db, solution_id, current_user)
    reference_tests = solution.prompt.reference_tests
    if not reference_tests:
        raise HTTPException(status_code=422, detail="Prompt has no reference tests to execute against")

    result_fields = run_solution_in_sandbox(solution.code, reference_tests)
    execution_result = crud.save_execution_result(db, solution_id=solution.id, **result_fields)

    return {
        "solution_id": solution.id,
        "passed_tests": execution_result.passed_tests,
        "total_tests": execution_result.total_tests,
        "pass_rate": execution_result.pass_rate,
        "runtime_seconds": execution_result.runtime_seconds,
        "error_type": execution_result.error_type,
    }
