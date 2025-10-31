PHARMORIS Backend — Detailed Documentation

Overview
--------
This document explains the project's goals, current implementation, how to run and test it, and recommended next steps and future enhancements.

Project Goal
------------
Build a FastAPI service with PostgreSQL + pgvector for semantic document search. Key requirements:
- /documents/search endpoint accepts a text query, runs cosine similarity (pgvector) and returns top 3 results.
- Celery + Redis worker pre-computes embeddings for documents.
- GDPR-compliant audit logging (hashed user ID, timestamp, action).
- Packaged with Docker and documented (README).

Status Summary
--------------
Overall: The code base implements the core features: FastAPI endpoints, pgvector integration, embedding generation (OpenAI or deterministic fallback), a Celery task path for precompute, and GDPR audit logging.

- PostgreSQL must run with the `pgvector` extension installed (or use an image such as `ankane/pgvector`). The app attempts to create the extension at startup, but the database container must allow creating extensions.
- Celery worker and Redis must be started for background processing to work reliably. If unavailable, embedding computation falls back to a synchronous attempt and/or documents may have NULL embeddings.
- Some DB drivers require the vector to be updated via an explicit SQL cast (`:emb::vector`). The code uses a safe insert-then-UPDATE approach and includes `app.utils.scripts.fill_embeddings` to backfill missing embeddings.

Repository Structure (high-level)
--------------------------------
- main.py — Application entry, middleware, router wiring, startup/shutdown hooks.
- api.py — Central router registry that includes feature routers (documents, monitoring, etc.).
- app/
  - db/initdb.py — SQLAlchemy async engine, session factory, Base, and `init_db()` that ensures `pgvector` extension and creates tables.
  - documents/
    - models.py — ORM models: `Document`, `AuditLog` (embedding defined as `Vector(1536)`).
    - schemas.py — Pydantic request/response schemas for documents and search.
    - router.py — FastAPI routes for `/documents` and `/documents/search` that call the service layer.
    - service.py — Business logic: create documents, compute embeddings, update DB safely with `:emb::vector`, perform vector search and fallback text search.
  - utils/
    - embeddings.py — `get_embedding()` uses OpenAI API if `OPENAI_API_KEY` is set, otherwise a deterministic fallback for dev/testing.
    - audit.py — `record_audit()` hashes user IDs with HMAC (uses `HMAC_KEY` from .env) and writes audit rows.
    - tasks.py — Celery task(s) for precomputing embeddings (enqueues `precompute_embeddings`).
  - core/
    - metrics.py — Prometheus metrics router and metrics definitions.
    - middleware.py — Metrics, rate limiting, and error handling middleware.
    - health.py — Health checks for DB, redis, and embedding service.

Other files
-----------
- app/utils/scripts/fill_embeddings.py — CLI script to compute & update embeddings for rows with NULL embedding (safe `:emb::vector` updates).
- README.md — Project README (contains quickstart and design decisions). Please review for secrets or missing instructions.
- requirements.txt — Python dependencies (ensure it contains `asyncpg`, `pgvector`, `prometheus-client`, `httpx`, `celery`, `redis`, etc.).
- docker-compose.yml — Services for db (Postgres + pgvector), redis, web, and worker. Ensure the compose file references an image with `pgvector` or sets `shared_preload_libraries` and proper extensions.

How the main flows work
-----------------------
Create document (POST /documents):
- Input: {title, content}
- Flow: `router -> DocumentService.create_document`.
  1. Compute embedding synchronously using `get_embedding()` (OpenAI if configured, else fallback).
  2. Prepare a Postgres vector literal string (e.g. "[0.1,0.2,...]").
  3. Insert the document row via ORM.
  4. If embedding available, perform a raw SQL update `UPDATE documents SET embedding = :emb::vector WHERE id = :id` to avoid driver adapter issues.
  5. If synchronous embedding computation fails, try to schedule `precompute_embeddings` Celery task. If Celery/Redis is unavailable, the document will have `embedding = NULL` until backfilled.
- Output: DocumentOut (id, title, content, optional score which is null on create).

Search documents (POST /documents/search):
- Input: {query, user_id?}
- Flow: `router -> DocumentService.search_documents`.
  1. Compute query embedding.
  2. Record an audit log row with hashed user id and action "search_documents".
  3. Perform pgvector search using `embedding <=> :query_embedding::vector` ORDER BY distance ASC LIMIT 3.
  4. If vector search fails (no embeddings or extension issue), fallback to full-text search via `to_tsvector(...) @@ plainto_tsquery(...)`.
- Output: SearchResponse { results: [DocumentOut] }. `score` currently holds the raw distance (lower = better). Consider converting to similarity for easier UX.

GDPR-audit logging
-------------------
- `app/utils/audit.py` uses HMAC-SHA256 with `HMAC_KEY` from `.env` to hash provided user IDs. Only the hashed value is stored in the audit table.
- Audit rows contain: `hashed_user_id`, `action`, `timestamp` (and optional metadata). Confirm the `AuditLog` model/DB table includes a `metadata` column if you intend to record additional JSON fields (current model may need JSONB column in schema).

OpenAI usage
------------
- `app/utils/embeddings.py` calls OpenAI by POSTing to `https://api.openai.com/v1/embeddings` with `model` set from `EMBEDDING_MODEL` and `input` equal to text. It expects `OPENAI_API_KEY` in the environment.
- If not set, deterministic fallback `_fallback_embedding()` is used (useful for offline testing). Do NOT use fallback in production.

Running the project (recommended local dev flow)
------------------------------------------------
Prerequisites:
- Docker Desktop running
- Git and Python 3.11+
- Your `.env` file configured (DATABASE_URL, REDIS_URL, OPENAI_API_KEY optional, HMAC_KEY)

1) Start DB and Redis (docker-compose recommended):
```cmd
# from repo root
docker-compose up -d db redis
# or run images individually
docker run -d --name pharmoris-db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=root123 -e POSTGRES_DB=openai -p 5432:5432 ankane/pgvector
docker run -d --name pharmoris-redis -p 6379:6379 redis:7
```

2) Create/verify .env (example values):
- DATABASE_URL=postgresql+asyncpg://postgres:root123@localhost:5432/openai
- REDIS_URL=redis://localhost:6379/0
- HMAC_KEY=replace_this_with_secure_random
- OPENAI_API_KEY=sk-...

3) Install Python deps and run server (venv):
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4) Start a Celery worker (so new documents are processed in background when applicable):
```cmd
# With venv active
celery -A app.utils.tasks worker --loglevel=info
```

5) Backfill missing embeddings (if you have existing documents with NULL embeddings):
```cmd
python -m app.utils.scripts.fill_embeddings
```

Testing and verification
------------------------
Unit/integration tests:
- The repo contains tests under `app/tests` or `tests/` (if present). Add pytest tests for:
  - create document (happy + embedding failure path)
  - search vector path (requires embeddings present)
  - search fallback text path (simulate missing embeddings)
  - audit logging hashing

Manual checks:
- Health endpoint: `GET /health` should report component statuses (database, redis, embedding_service). If DB reports `type "vector" does not exist`, ensure pgvector extension is present.
- Metrics: `GET /metrics` for Prometheus output.
- DB: query `SELECT id, embedding IS NULL AS missing FROM documents ORDER BY id DESC LIMIT 10;`


Future enhancements
-------------------------------------------------------
1. Integrate pgvector adapter with asyncpg to allow assigning Python lists directly to `Document.embedding`.
2. Add end-to-end tests and CI (actions to run tests, linters).
3. Implement `POST /admin/fill-embeddings` protected by API key for on-demand backfill.
4. Add a metric for embedding backlog (count of documents with NULL embedding) and Grafana alerts.
5. Convert search distance into a similarity score and add relevance tuning options (filters, facets).
6. Add rate limiting with Redis and distributed locks for scaling.
7. Add integration tests using a Testcontainers-style setup or docker-compose test profile.
