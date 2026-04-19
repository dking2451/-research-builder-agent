# Research Builder Agent (V1)

A personal **research + reasoning + builder** workbench: capture questions, run structured workflows (Research / Decide / Build / Learn), persist evidence-shaped memory (facts, findings, sources, artifacts, tasks), and revisit it over time.

This folder is intentionally isolated from other apps in the repo:

- `backend/` — FastAPI + SQLAlchemy + Alembic + OpenAI structured outputs
- `frontend/` — Next.js (App Router) + TypeScript + Tailwind

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 14+ (recommended; JSONB + UUID)

## Backend setup

```bash
cd research-builder-agent/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

1. Create a database (example): `createdb research_builder`
2. Set `DATABASE_URL` in `.env` (see `.env.example`)
3. Run migrations:

```bash
alembic upgrade head
```

This includes `20260418_0002` (knowledge `importance_score` / `is_pinned` + `knowledge_item_relations`), `20260418_0003` (verification / evidence strength + citation links on `knowledge_items`), `20260418_0004` (`knowledge_items.is_archived` for soft-archive), and `20260418_0005` (`task_items.metadata_json`, artifact `is_pinned` / `importance_score`).

4. (Optional) Seed demo content:

```bash
python -m scripts.seed_demo
```

5. Run API:

```bash
uvicorn app.main:app --reload --port 8000
```

6. Run backend tests:

```bash
cd research-builder-agent/backend
PYTHONPATH=. pytest tests/test_context_assembly_service.py -v
```

### OpenAI configuration

Set `OPENAI_API_KEY` in `backend/.env`.

If you want to exercise the UI without calling OpenAI, set:

- `USE_STUB_AGENT=true`

## Frontend setup

```bash
cd research-builder-agent/frontend
cp .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL` to your API origin (default `http://localhost:8000`).

## Core API surface (V1)

- `GET /health`
- `GET /dashboard`
- Projects: `POST/GET/PATCH /projects`, `POST/GET /projects/{id}/conversations`
- Conversations: `GET /conversations/{id}`, `POST /conversations/{id}/messages`
- Agent: `POST /agent/run`
- Knowledge: `GET/POST /projects/{id}/knowledge`, `GET /knowledge/library`, `GET/PATCH/DELETE /knowledge/{id}`
- Artifacts: `GET/POST /projects/{id}/artifacts`, `GET /artifacts/library`, `GET /artifacts/{id}`
- Tasks: `GET/POST /projects/{id}/tasks`, `PATCH /tasks/{id}`
- Search: `GET /search?q=...`

## Architecture (how it fits together)

- **Routes (`app/api/`)** validate ownership via a single default user (`DEFAULT_USER_EMAIL`) for V1.
- **Orchestrator (`app/services/orchestrator.py`)** writes the user message, calls OpenAI via `beta.chat.completions.parse` into `AgentLLMEnvelope`, writes assistant message, persists sources/knowledge/artifacts/tasks.
- **Mode prompts (`app/prompts/mode_prompts.py`)** enforce evidence-first behavior + required JSON shape.
- **Extraction (`app/services/knowledge_extraction_service.py`)** normalizes unsafe/unknown knowledge types.

## Future-friendly hooks

- **Embeddings / semantic search**: `knowledge_items.embedding_ref` is ready for “vector row id” or “external store key”; add `pgvector` + a background job when you outgrow keyword search.
- **Web research**: add a tool/service that writes `SourceRecord` + `KnowledgeItem` citations; keep the orchestrator thin.
- **File ingestion**: store files in object storage, summarize into `KnowledgeItem` + `GeneratedArtifact`, and link via `metadata_json`.
