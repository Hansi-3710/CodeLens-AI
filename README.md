# LLM Code Intelligence Platform

An AI evaluation and analysis system that investigates how different LLMs
solve the same programming problems, and compares their solutions on
correctness, efficiency, style, and structural diversity.

Research question: *How different are the solutions produced by modern
LLMs when solving the same programming tasks, and how do correctness,
efficiency, and style vary?*

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full system design,
database schema, and API contracts, and [`DEPLOYMENT.md`](./DEPLOYMENT.md)
for how to ship it.

## Status: all 9 phases complete

| Phase | Status |
|---|---|
| 1 — Architecture | ✅ |
| 2 — Backend Foundation (auth, CRUD) | ✅ |
| 3 — Database (migrations, seed, pooling) | ✅ |
| 4 — LLM Services (OpenAI/HF/local providers) | ✅ |
| 5 — Execution Sandbox (Docker) | ✅ |
| 6 — ML & Analysis (AST, complexity, style, similarity, embeddings, clustering, classification, statistics) | ✅ |
| 7 — Frontend (all pages, real API integration) | ✅ |
| 8 — Testing (77 backend + 6 frontend tests) | ✅ |
| 9 — Deployment (Vercel + Render configs) | ✅ |

**Verified in this build environment:** 76/77 backend tests pass (1
integration test correctly auto-skips — no Docker daemon here), full
lint-clean, Alembic migration applies cleanly, frontend typechecks,
production-builds, and passes its Jest suite. See
[`DEPLOYMENT.md`](./DEPLOYMENT.md#what-s-verified-vs-what-needs-real-infrastructure-to-confirm)
for the honest boundary of what still needs real Docker/Postgres/API-key
infrastructure to confirm end-to-end.

## Quickstart

```bash
# Backend
cd backend
cp .env.example .env   # add OPENAI_API_KEY / HUGGINGFACE_API_TOKEN
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py       # registers gpt-4, gpt-4o-mini, llama-3-70b, gemma-7b
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Or via Docker Compose (backend + Postgres + frontend):

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173

To run generated code (`POST /solutions/{id}/execute`), also build the
sandbox image once: `docker build -t llm-code-intel-sandbox:latest ./backend/sandbox`
(see `backend/sandbox/README.md`).

## Running the tests

```bash
# Backend
cd backend && PYTHONPATH=. pytest -v --cov=app --cov-report=term-missing

# Frontend
cd frontend && npx jest
```

## Project structure

```
llm-code-intelligence/
├── backend/app/
│   ├── api/v1/           # HTTP routers: auth, experiments, solutions, analytics, models
│   ├── llm/               # Provider-agnostic LLM generation (OpenAI/HF/local, Strategy pattern)
│   ├── execution/          # Docker sandbox for running untrusted generated code
│   ├── analysis/            # AST, complexity, style, similarity
│   ├── ml/                   # Embeddings, clustering, classification, statistics
│   ├── evaluation/            # Problem sets + metric aggregation (MODEL COMPARISON view)
│   └── database/               # SQLAlchemy models, Pydantic schemas, session, CRUD
├── backend/alembic/              # DB migrations
├── backend/sandbox/                # Docker image for code execution
├── frontend/src/
│   ├── api/                          # axios client + React Query hooks
│   ├── components/                    # ModelChannelTag, Leaderboard, Chart, SimilarityHeatmap, CodeViewer, MetricCard
│   └── pages/                          # Dashboard, CreateExperiment, ExperimentResults, ModelComparison, Visualization, Login
├── datasets/                             # Hand-written problem set (custom_problems.json)
├── docker-compose.yml
├── render.yaml                             # Backend deployment (Render Blueprint)
└── frontend/vercel.json                     # Frontend deployment (Vercel)
```
