# LLM Code Intelligence Platform — Architecture (Phase 1)

Research question this platform answers: *how different are the solutions
produced by modern LLMs when solving the same programming tasks, and how do
correctness, efficiency, and style vary?*

This is an AI **evaluation and analysis system**, not a chatbot. A user
defines an experiment (a set of problems + a set of models), the platform
generates solutions, executes and analyzes them, and visualizes how the
models compare and diverge.

---

## 1. System Overview

```
                    React Frontend (TS, Tailwind, Recharts/Plotly, React Flow)
                                       |
                                  REST / JSON
                                       |
                              FastAPI Backend
                                       |
        -----------------------------------------------------------
        |              |               |              |           |
   LLM Manager   Execution Sandbox  Analysis Engine  ML Pipeline  Database
        |              |               |              |           |
   OpenAI /       Docker container   AST / Radon /   Embeddings /   PostgreSQL
   HF / Local     (isolated, no      flake8/pylint   Clustering /
   providers      network, capped)                   Classification /
                                                       Statistics
```

Five backend subsystems, each independently testable:

| Subsystem | Responsibility | Depends on |
|---|---|---|
| LLM Manager | Fan a prompt out to N models concurrently, normalize responses | Nothing (pure I/O layer) |
| Execution Sandbox | Run generated code safely, report pass/fail + runtime + memory | Docker |
| Analysis Engine | Static facts about code: AST shape, complexity, style | Nothing (pure functions) |
| ML Pipeline | Embeddings, clustering, classification, statistics *across* solutions | Analysis Engine + Execution results |
| Database | Persist everything above, serve aggregated views to the API | All of the above write to it |

---

## 2. Key Design Decisions

**Provider abstraction (Strategy pattern) for LLMs.**
`BaseLLMProvider` defines `generate_code()`, `get_model_info()`,
`estimate_cost()`. `LLMManager` only knows this interface. Adding a new
model — a new OpenAI model, a HF-hosted model, a locally-run model — means
adding one file under `llm/providers/`, never touching the manager, the API
layer, or the database. This is the single decision that keeps "compare N
models" from becoming N special cases scattered through the codebase.

**Docker sandbox is a hard boundary, not a convenience.**
Generated code is untrusted by definition — it's the *output* of an LLM,
not code the developer wrote. It never runs in the FastAPI process. It runs
in a container with `network_disabled=True`, a memory cap, and a wall-clock
timeout, and the container is destroyed after each run. The backend talks
to Docker over the socket mounted in `docker-compose.yml`; if this line
were removed, no generated code could execute at all — that's intentional
so the security boundary is a deployment fact, not just an application
convention.

**Execution and static analysis are separate, independently-retryable
pipelines.**
`ExecutionResult` and `AnalysisResult` are separate 1:1 tables off
`GeneratedSolution`, not columns bolted onto it. Execution is slow,
sandboxed, and can legitimately fail (timeout, OOM). Analysis is fast,
in-process, and safe to run eagerly. Splitting them means a sandbox failure
doesn't block style/complexity results from showing up, and either
pipeline can be re-run independently without re-doing the other.

**Embeddings stored as JSON now, `pgvector`-ready later.**
For a research-scale platform (hundreds–low thousands of solutions per
experiment), a JSON float array column plus in-Python cosine similarity is
simpler to run locally and easier to inspect than standing up `pgvector`.
Because all embedding access goes through `database/crud.py`, swapping the
column type and query implementation later doesn't touch any calling code.

**Similarity has three methods because they answer different questions.**
Token similarity (`difflib`) catches near-duplicate code. AST similarity
catches structurally-equivalent code with different variable names. Embedding
similarity catches *semantically* similar solutions that look nothing alike
token-for-token (e.g. iterative vs. recursive). Reporting only one would
misrepresent what "similar" means — the heatmap in the UI should let the
user pick the lens.

**Model-fingerprint classification is diagnostic, not a feature.**
Training a classifier to guess which model wrote a solution (Random Forest
on embedding + style + complexity features) directly operationalizes "how
distinct are these models' styles?" — a classifier that can't beat chance
means the models are stylistically indistinguishable on this problem set;
one that hits 90%+ means they have a strong fingerprint. This is reported
with cross-validated accuracy, not a single train/test split, since
per-experiment sample sizes will often be small.

**Async generation from the start.**
`POST /experiments/{id}/generate` fans out to every selected model with
`asyncio.gather` and per-provider error isolation — one model timing out or
erroring must not fail the batch for the others. `Experiment.status` moves
`pending → running → completed|failed` so the frontend can poll without the
request itself blocking for the slowest model.

---

## 3. Folder Structure

```
llm-code-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, router registration, CORS
│   │   ├── config.py               # Settings (env-driven)
│   │   ├── api/v1/
│   │   │   ├── experiments.py      # POST /experiments, .../generate, .../results
│   │   │   ├── solutions.py        # GET /solutions/{id}, POST .../execute
│   │   │   ├── analytics.py        # GET /analytics/{id}[/similarity|/clusters]
│   │   │   └── models.py           # GET/POST /models (model registry)
│   │   ├── core/
│   │   │   ├── logging.py
│   │   │   └── security.py         # auth (JWT)
│   │   ├── llm/
│   │   │   ├── base_provider.py    # BaseLLMProvider interface + GenerationResult
│   │   │   ├── llm_manager.py      # fans prompt out to N providers concurrently
│   │   │   └── providers/
│   │   │       ├── openai_provider.py
│   │   │       ├── huggingface_provider.py
│   │   │       └── local_model_provider.py
│   │   ├── execution/
│   │   │   ├── docker_worker.py    # spins up isolated container
│   │   │   ├── sandbox_runner.py   # builds test harness, invokes docker_worker
│   │   │   └── result_parser.py    # raw sandbox output -> ExecutionResult
│   │   ├── analysis/
│   │   │   ├── ast_analyzer.py     # AST -> structured, comparable summary
│   │   │   ├── complexity.py       # radon: cyclomatic complexity, MI, Big-O estimate
│   │   │   ├── style_checker.py    # flake8/pylint, docstring coverage
│   │   │   └── similarity.py       # token / AST / embedding similarity
│   │   ├── ml/
│   │   │   ├── embeddings.py       # Sentence-Transformers / CodeBERT
│   │   │   ├── clustering.py       # KMeans, DBSCAN, UMAP projection
│   │   │   ├── classification.py   # Random Forest: predict model from code
│   │   │   └── statistics.py       # mean/median/CI/correlation
│   │   ├── evaluation/
│   │   │   ├── tester.py           # problem sets + reference tests
│   │   │   └── metrics.py          # per-model aggregate metrics
│   │   └── database/
│   │       ├── models.py           # SQLAlchemy ORM (schema of record)
│   │       ├── schemas.py          # Pydantic request/response contracts
│   │       ├── session.py          # engine/session, get_db() dependency
│   │       └── crud.py             # all raw queries
│   ├── alembic/                    # migrations
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── MetricCard.tsx
│       │   ├── Chart.tsx
│       │   ├── CodeViewer.tsx
│       │   ├── SimilarityHeatmap.tsx
│       │   └── Leaderboard.tsx
│       ├── pages/
│       │   ├── Login.tsx
│       │   ├── Dashboard.tsx
│       │   ├── CreateExperiment.tsx
│       │   ├── ExperimentResults.tsx
│       │   ├── ModelComparison.tsx
│       │   └── Visualization.tsx
│       ├── graphs/                 # UMAP scatter, heatmap, leaderboard chart impls
│       ├── api/                    # React Query hooks
│       └── types/index.ts          # mirrors backend/app/database/schemas.py
├── datasets/                       # HumanEval, MBPP, custom problems
├── .github/workflows/ci.yml
├── docker-compose.yml
└── README.md
```

Every non-trivial file in the tree above already exists in the repo with a
docstring stating its purpose and which phase implements it — nothing here
is aspirational, it's scaffolded and importable today (verified: the
FastAPI app boots, all 9 ORM tables register correctly, and the two Phase-1
tests pass).

---

## 4. Database Schema

9 tables, PostgreSQL, SQLAlchemy ORM (`backend/app/database/models.py`):

```
users
 └─< experiments
      └─< prompts
           └─< generated_solutions >──── ai_models
                ├──1:1── execution_results
                ├──1:1── analysis_results
                └──1:1── embeddings

similarity_scores  (solution_a_id, solution_b_id -> generated_solutions, M:N)
```

| Table | Key columns | Notes |
|---|---|---|
| `users` | email, hashed_password | Phase 2 auth |
| `experiments` | owner_id, name, status | status: pending→running→completed/failed |
| `ai_models` | name, provider, version | registry, `is_active` toggles availability |
| `prompts` | experiment_id, problem_statement, reference_tests (JSON), source_dataset | one prompt → many solutions (one per model) |
| `generated_solutions` | prompt_id, model_id, code, tokens_used, latency | the core "N models × M prompts" fact table |
| `execution_results` | passed_tests, pass_rate, runtime_seconds, memory_mb, error_type | 1:1, sandbox output |
| `analysis_results` | cyclomatic_complexity, big_o_estimate, style_score, ast_summary (JSON) | 1:1, static analysis output |
| `embeddings` | vector (JSON), cluster_label | 1:1, feeds similarity + clustering |
| `similarity_scores` | solution_a_id, solution_b_id, token/ast/embedding similarity | pairwise, computed per prompt group |

All primary keys are UUID strings (safe to expose in URLs, no cross-environment
collisions). Full column list is in the source file, not duplicated here to
avoid the two drifting out of sync.

---

## 5. API Contracts

All endpoints are scaffolded in `backend/app/api/v1/` today and return
`501` with the phase that will implement them, so the frontend can be built
against a stable contract before the logic exists.

### `POST /experiments`
```json
// Request
{
  "name": "Shortest path comparison",
  "description": "optional",
  "prompts": [
    { "problem_statement": "Implement a function that finds the shortest path between two nodes.", "language": "python" }
  ],
  "models": ["gpt-4", "llama-3-70b", "gemma-7b"]
}
// Response (201)
{ "id": "uuid", "name": "...", "status": "pending", "created_at": "..." }
```

### `POST /experiments/{id}/generate`
Triggers async generation across every selected model for every prompt in
the experiment. Returns immediately with `status: "running"`; poll
`GET /experiments/{id}/results` or `GET /experiments/{id}`.

### `GET /experiments/{id}/results`
```json
{
  "experiment_id": "uuid",
  "status": "completed",
  "models": [
    { "model": "gpt-4",       "correctness": 0.96, "avg_runtime_s": 0.03, "complexity": "O(V+E)" },
    { "model": "llama-3-70b", "correctness": 0.88, "avg_runtime_s": 0.05, "complexity": "O(V^2)" },
    { "model": "gemma-7b",    "correctness": 0.90, "avg_runtime_s": 0.04, "complexity": "O(V+E)" }
  ]
}
```

### `POST /solutions/{id}/execute`
Runs one solution through the Docker sandbox on demand (e.g. re-run after a
flaky timeout). Returns an `ExecutionResult`.

### `GET /analytics/{experiment_id}` / `.../similarity` / `.../clusters`
Returns the statistics summary, the pairwise similarity matrix (for the
heatmap), and the 2D UMAP projection + cluster labels (for the diversity
map), respectively.

### `GET /models` / `POST /models`
List or register models available for selection when creating an experiment.

---

## 6. Development Milestones

| Phase | Deliverable | Depends on |
|---|---|---|
| **1 — Architecture** *(this document)* | Design decisions, folder structure, schema, contracts, milestones, test strategy | — |
| **2 — Backend Foundation** | Auth, DB-backed CRUD for experiments/models, real routers replacing 501 stubs, logging | Phase 1 |
| **3 — Database** | Alembic migrations, seed data, `crud.py` implementation, connection pooling | Phase 2 |
| **4 — LLM Services** | Implement all 3 providers, `LLMManager.generate_all()`, wire `/generate` | Phase 2 |
| **5 — Execution Sandbox** | Docker worker, sandbox image, test harness renderer, wire `/execute` | Phase 3 |
| **6 — ML & Analysis** | AST/complexity/style analyzers, embeddings, clustering, classifier, statistics, wire `/analytics` | Phase 3, 5 |
| **7 — Frontend** | All pages/components, React Query hooks against the now-real API | Phase 4, 5, 6 |
| **8 — Testing** | Full pytest suite (unit + integration + sandbox safety), Jest suite, coverage gates in CI | All above |
| **9 — Deployment** | Frontend → Vercel, backend → Render/AWS, managed Postgres, secrets | Phase 8 |

Each phase ends with: a summary of what was completed, what's left, and a
check that the implementation still matches this document (or an explicit,
explained deviation from it).

---

## 7. Testing Strategy

- **Backend unit tests** (`pytest`): pure-function modules — `analysis/*`,
  `ml/statistics.py`, `llm/base_provider.py` dataclasses — tested with no
  DB or network.
- **Backend integration tests**: API routes tested via `TestClient` against
  a disposable test Postgres (spun up in CI as a service container, see
  `.github/workflows/ci.yml`).
- **Sandbox safety tests**: dedicated tests asserting the execution
  container cannot reach the network, cannot exceed its memory cap, and is
  killed on timeout — these are security tests, not just functional ones,
  and should never be skipped in CI.
- **Frontend tests** (`Jest`): component rendering + hook behavior against
  mocked API responses matching `frontend/src/types/index.ts`.
- **CI gate**: every PR runs backend lint (`flake8`) + `pytest`, and
  frontend lint + `jest`, before merge (`.github/workflows/ci.yml`, already
  in the repo).

Current test status: 2/2 passing (`backend/tests/test_health.py`) — the app
boots, CORS/router wiring is correct, and stub routes fail loudly (`501`)
rather than silently (`500`), which is the property this phase needed to
prove before any real logic is written.

---

## 8. Final Project Summary (all 9 phases complete)

**Phase 1 — Architecture:** design decisions, schema, contracts, milestones
documented above; repository scaffold created.

**Phase 2 — Backend Foundation:** JWT auth (register/login,
`get_current_user` dependency, bcrypt hashing), full CRUD for users,
models, experiments, and solutions, structured logging. Every route that
was a `501` stub in Phase 1 now has a real implementation.

**Phase 3 — Database:** Alembic migration generated and verified to apply
cleanly (9 tables + `alembic_version`), connection pool tuning
(`pool_size`/`max_overflow`/`pool_recycle` for Postgres), and a seed script
(`scripts/seed.py`) registering gpt-4, gpt-4o-mini, llama-3-70b, gemma-7b.

**Phase 4 — LLM Services:** `OpenAIProvider`, `HuggingFaceProvider`, and
`LocalModelProvider` all implement `BaseLLMProvider`; `LLMManager.generate_all()`
fans a prompt out to every selected model concurrently with per-provider
error isolation (one model failing never fails the batch). Wired into
`POST /experiments/{id}/generate`, which also runs static analysis eagerly
on each solution as it's saved.

**Phase 5 — Execution Sandbox:** `DockerWorker` runs generated code in a
network-disabled, memory-capped, timeout-enforced container; `sandbox_runner.py`
builds the pytest harness from a prompt's reference tests; `result_parser.py`
turns pytest's JSON report into an `ExecutionResult`. Wired into
`POST /solutions/{id}/execute`.

**Phase 6 — ML & Code Analysis:** AST analysis (node histograms, loop
nesting depth, recursion detection), radon-based complexity + a documented
Big-O heuristic, flake8-based style checking + docstring coverage,
three-method similarity (token/AST/embedding), Sentence-Transformer
embeddings, KMeans/DBSCAN/UMAP clustering, a cross-validated Random Forest
model-fingerprint classifier, and statistics (mean/median/CI/correlation).
Wired into `GET /experiments/{id}/results` (the MODEL COMPARISON view) and
`GET /analytics/{id}[/similarity|/clusters]`.

**Phase 7 — Frontend:** every page and component is a real implementation,
not a stub — Login, Dashboard, CreateExperiment, ExperimentResults,
ModelComparison (side-by-side code diffing), and Visualization (stats +
similarity heatmap + diversity map), all wired to the live API via React
Query hooks. Ships a deliberate design language (see `frontend-design`
notes: an oscilloscope/lab-notebook palette where each model gets a
consistent "channel" color across every visualization — the leaderboard,
the heatmap, and the diversity map all use the same color for the same
model, which is the actual point of a model-comparison tool).

**Phase 8 — Testing:** 77 backend tests (76 passing, 1 real-Docker
integration test that correctly auto-skips without a daemon), 88% backend
line coverage, 6 frontend Jest tests, full `flake8` lint pass, and CI
(`.github/workflows/ci.yml`) that applies the real Alembic migration
against a live Postgres service container before running anything else.

**Phase 9 — Deployment:** `frontend/vercel.json` and `render.yaml` are
ready to deploy from; `DEPLOYMENT.md` documents the one piece of
infrastructure that doesn't fit a typical PaaS — the execution sandbox
needs a reachable Docker daemon — with two concrete options for handling
it in production.

**What's genuinely verified vs. what needs real infrastructure:** this
entire build ran in a sandbox with no Docker daemon, no Postgres server,
and no network egress to openai.com/huggingface.co. Every line of business
logic is real and tested against mocks/SQLite/a fake provider where live
infrastructure wasn't available — see `DEPLOYMENT.md`'s verification table
for the exact boundary between "tested here" and "needs a live service to
confirm." Nothing was left as a placeholder; the gaps are infrastructure
access, not unwritten code.

