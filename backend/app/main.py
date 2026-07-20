"""
FastAPI application entrypoint.

Belongs to: backend/app/
"""
import logging
import uuid

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import auth, experiments, solutions, analytics, models
from app.config import get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import limiter

configure_logging()
logger = logging.getLogger(__name__)
settings = get_settings()
settings.validate_for_production()

app = FastAPI(
    title=settings.APP_NAME,
    description="Evaluates and analyzes AI-generated code across multiple LLMs.",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Restricted to what the API actually uses. `allow_methods=["*"]` /
# `allow_headers=["*"]` are a common default that's broader than this API
# needs — every route here is GET or POST, and the only custom header the
# frontend sends is Authorization.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Tags every request/response with a correlation ID, logged alongside
    any error — without this, matching a user's bug report ("it 500'd at
    2pm") back to a specific log line is guesswork."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """FastAPI's default 422 body already omits internals, but this keeps
    the shape consistent with the handler below and adds the request ID."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "request_id": getattr(request.state, "request_id", None)},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catches anything that isn't an HTTPException (which FastAPI already
    handles cleanly). Without this, an unexpected exception's full Python
    traceback — file paths, variable values, sometimes DB connection
    strings in a repr — goes straight into the HTTP response body whenever
    `debug`-style tracebacks leak, which is a real information-disclosure
    risk, not a hypothetical one. The real exception is still logged
    server-side with its full traceback via `exc_info=True`; the client
    only gets a generic message plus a request ID to report.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("Unhandled exception on request %s", request_id, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "request_id": request_id},
    )


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
app.include_router(solutions.router, prefix="/solutions", tags=["solutions"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(models.router, prefix="/models", tags=["models"])


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Basic liveness probe used by Docker/CI."""
    return {"status": "ok", "service": settings.APP_NAME}
