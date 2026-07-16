"""
Registration and login. Issues JWTs consumed by core/security.get_current_user.

Belongs to: backend/app/api/v1/
Phase: 2 (Backend Foundation)

Contract:
  POST /auth/register  -> create a user
  POST /auth/login     -> OAuth2 password flow, returns {access_token, token_type}
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.database import crud, schemas
from app.database.session import get_db

router = APIRouter()


@router.post("/register", response_model=schemas.UserRead, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user = crud.create_user(db, payload.email, payload.password, payload.full_name)
    return user


@router.post("/login", response_model=schemas.Token)
@limiter.limit("10/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}
