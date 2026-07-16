"""
Registry of AI models available to select in an experiment.

Belongs to: backend/app/api/v1/
Phase: 2 (Backend Foundation)
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import crud, schemas
from app.database.session import get_db

router = APIRouter()


@router.get("", response_model=list[schemas.ModelRead])
def list_models(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    limit = min(limit, 100)
    return crud.list_models(db, skip=skip, limit=limit)


@router.post("", response_model=schemas.ModelRead, status_code=201)
def register_model(payload: schemas.ModelCreate, db: Session = Depends(get_db)):
    return crud.create_model(db, payload.name, payload.provider, payload.version, payload.context_window)
