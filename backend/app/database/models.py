"""
SQLAlchemy ORM models — the canonical database schema for the platform.

Belongs to: backend/app/database/
Defined in: Phase 1 (Architecture). Migrated via Alembic in Phase 3 (Database).

Design notes:
- UUID primary keys (not auto-increment ints) so experiment/solution IDs are
  safe to expose in URLs and won't collide across environments.
- Embeddings are stored as JSON float arrays for now. If the dataset grows
  large, swap to the `pgvector` extension + a Vector column without changing
  any calling code, since access goes through database/crud.py.
- Execution and Analysis are separate 1:1 tables off GeneratedSolution rather
  than columns on it, so the sandbox (untrusted, slower) and static analysis
  (trusted, fast) pipelines can run independently and be retried separately.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    experiments = relationship("Experiment", back_populates="owner")


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending | running | completed | failed
    selected_models = Column(JSON, nullable=False, default=list)  # list[str] of AIModel.name
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="experiments")
    prompts = relationship("Prompt", back_populates="experiment", cascade="all, delete-orphan")


class AIModel(Base):
    """A registered LLM under test (e.g. gpt-4, llama-3-70b, gemma-7b)."""
    __tablename__ = "ai_models"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name = Column(String, unique=True, nullable=False)
    provider = Column(String, nullable=False)  # openai | huggingface | local
    version = Column(String, nullable=True)
    context_window = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    experiment_id = Column(UUID(as_uuid=False), ForeignKey("experiments.id"), nullable=False, index=True)
    problem_statement = Column(Text, nullable=False)
    language = Column(String, default="python")
    difficulty = Column(String, nullable=True)  # easy | medium | hard
    reference_tests = Column(JSON, nullable=True)  # [{"input": ..., "expected_output": ...}]
    source_dataset = Column(String, nullable=True)  # HumanEval | MBPP | custom

    experiment = relationship("Experiment", back_populates="prompts")
    solutions = relationship("GeneratedSolution", back_populates="prompt", cascade="all, delete-orphan")


class GeneratedSolution(Base):
    __tablename__ = "generated_solutions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    prompt_id = Column(UUID(as_uuid=False), ForeignKey("prompts.id"), nullable=False, index=True)
    model_id = Column(UUID(as_uuid=False), ForeignKey("ai_models.id"), nullable=False, index=True)
    code = Column(Text, nullable=False)
    raw_response = Column(Text, nullable=True)
    temperature = Column(Float, default=0.2)
    max_tokens = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    generation_latency_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    prompt = relationship("Prompt", back_populates="solutions")
    model = relationship("AIModel")
    execution_result = relationship(
        "ExecutionResult", back_populates="solution", uselist=False, cascade="all, delete-orphan"
    )
    analysis_result = relationship(
        "AnalysisResult", back_populates="solution", uselist=False, cascade="all, delete-orphan"
    )
    embedding = relationship(
        "Embedding", back_populates="solution", uselist=False, cascade="all, delete-orphan"
    )


class ExecutionResult(Base):
    __tablename__ = "execution_results"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    solution_id = Column(
        UUID(as_uuid=False), ForeignKey("generated_solutions.id"), nullable=False, unique=True, index=True
    )
    passed_tests = Column(Integer, default=0)
    total_tests = Column(Integer, default=0)
    pass_rate = Column(Float, default=0.0)
    runtime_seconds = Column(Float, nullable=True)
    memory_mb = Column(Float, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    error_type = Column(String, nullable=True)
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    solution = relationship("GeneratedSolution", back_populates="execution_result")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    solution_id = Column(
        UUID(as_uuid=False), ForeignKey("generated_solutions.id"), nullable=False, unique=True, index=True
    )
    lines_of_code = Column(Integer, nullable=True)
    cyclomatic_complexity = Column(Float, nullable=True)
    big_o_estimate = Column(String, nullable=True)
    maintainability_index = Column(Float, nullable=True)
    style_score = Column(Float, nullable=True)
    pep8_violations = Column(Integer, nullable=True)
    docstring_coverage = Column(Float, nullable=True)
    ast_summary = Column(JSON, nullable=True)  # node-type histogram / tree shape

    solution = relationship("GeneratedSolution", back_populates="analysis_result")


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    solution_id = Column(
        UUID(as_uuid=False), ForeignKey("generated_solutions.id"), nullable=False, unique=True, index=True
    )
    model_name = Column(String, default="sentence-transformers/all-MiniLM-L6-v2")
    vector = Column(JSON, nullable=False)  # list[float]
    cluster_label = Column(Integer, nullable=True)

    solution = relationship("GeneratedSolution", back_populates="embedding")


class SimilarityScore(Base):
    """Pairwise similarity between two solutions to the same prompt."""
    __tablename__ = "similarity_scores"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    solution_a_id = Column(UUID(as_uuid=False), ForeignKey("generated_solutions.id"), nullable=False, index=True)
    solution_b_id = Column(UUID(as_uuid=False), ForeignKey("generated_solutions.id"), nullable=False, index=True)
    token_similarity = Column(Float, nullable=True)
    ast_similarity = Column(Float, nullable=True)
    embedding_similarity = Column(Float, nullable=True)
