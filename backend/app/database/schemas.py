"""
Pydantic schemas — request/response contracts for the API layer.
Kept separate from database/models.py (ORM) so the wire format can evolve
independently of storage (e.g. hiding internal fields, renaming for the client).

Belongs to: backend/app/database/
Phase: 1 (contracts defined) -> Phase 4/5 (wired into live endpoints).
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---- Auth -----------------------------------------------------------------

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserRead(BaseModel):
    id: str
    email: str
    full_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- AI Models -----------------------------------------------------------------

class ModelCreate(BaseModel):
    name: str
    provider: str = Field(..., description="openai | huggingface | local")
    version: str | None = None
    context_window: int | None = None


class ModelRead(BaseModel):
    id: str
    name: str
    provider: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ---- Experiments -----------------------------------------------------------------

class PromptCreate(BaseModel):
    problem_statement: str
    language: str = "python"
    difficulty: str | None = None
    reference_tests: list[dict] | None = None
    source_dataset: str | None = None


class ExperimentCreate(BaseModel):
    name: str
    description: str | None = None
    prompts: list[PromptCreate]
    models: list[str] = Field(..., description="Registered AIModel names, e.g. ['gpt-4','llama-3-70b']")


class ExperimentRead(BaseModel):
    id: str
    name: str
    status: str
    selected_models: list[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SolutionRead(BaseModel):
    id: str
    model_name: str
    code: str
    pass_rate: float | None = None
    runtime_seconds: float | None = None
    cyclomatic_complexity: float | None = None

    model_config = ConfigDict(from_attributes=True)


class GenerateRequest(BaseModel):
    experiment_id: str
    temperature: float = 0.2
    max_tokens: int = 1024


class GenerateResponse(BaseModel):
    experiment_id: str
    status: str


class SolutionSummary(BaseModel):
    id: str
    prompt_id: str
    problem_statement: str
    model_name: str
    code: str


class ExecuteResponse(BaseModel):
    solution_id: str
    passed_tests: int
    total_tests: int
    pass_rate: float
    runtime_seconds: float | None
    error_type: str | None


# ---- Results / Analytics -----------------------------------------------------------------

class ModelComparisonRow(BaseModel):
    model: str
    correctness: float | None
    correctness_ci_95: list[float | None]
    avg_runtime_s: float | None
    complexity: str | None
    n_solutions: int


class ExperimentResultsResponse(BaseModel):
    experiment_id: str
    status: str
    models: list[ModelComparisonRow]


class DescriptiveStats(BaseModel):
    mean: float | None
    median: float | None
    stdev: float | None
    ci_95_low: float | None
    ci_95_high: float | None
    n: int


class CorrelationResult(BaseModel):
    pearson_r: float | None
    pearson_p: float | None
    spearman_r: float | None
    spearman_p: float | None
    n: int


class ModelFingerprintResult(BaseModel):
    cv_accuracy: float | None = None
    cv_accuracy_std: float | None = None
    n_samples: int | None = None
    n_classes: int | None = None
    baseline_accuracy: float | None = None
    sufficient_data: bool


class AnalyticsSummary(BaseModel):
    experiment_id: str
    n_solutions: int
    code_length: DescriptiveStats
    pass_rate: DescriptiveStats
    cyclomatic_complexity: DescriptiveStats
    correlations: dict[str, CorrelationResult]
    model_fingerprint: ModelFingerprintResult


class SimilarityPair(BaseModel):
    prompt_id: str
    model_a: str
    model_b: str
    token_similarity: float
    ast_similarity: float
    embedding_similarity: float | None


class SimilarityMatrixResponse(BaseModel):
    experiment_id: str
    pairs: list[SimilarityPair]


class ClusterPoint(BaseModel):
    solution_id: str
    model: str
    prompt_id: str
    x: float
    y: float
    cluster: int


class ClustersResponse(BaseModel):
    experiment_id: str
    points: list[ClusterPoint]
    method: str | None = None
    note: str | None = None
