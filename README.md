# PHARMORIS™ v0.9 - Backend (FastAPI + PostgreSQL + pgvector + Celery)

## Features
- FastAPI service with /documents endpoints and vector search (/documents/search)
- PostgreSQL with pgvector for efficient similarity search
- Celery + Redis worker for background embedding computation
- GDPR-compliant audit logging (hashed user IDs, timestamps, actions)
- Docker + docker-compose for easy deployment

## Architecture & Design Decisions
- **Vector Search**: Using pgvector for efficient similarity search with cosine distance
- **Async Processing**: Celery worker precomputes embeddings to avoid blocking API requests
- **GDPR Compliance**: User IDs are hashed using HMAC-SHA256 before storage
- **Scalability**: Horizontally scalable with multiple workers and API instances

## Quickstart (dev)
1. Copy `.env.example` to `.env` and set values
2. Build & start services:
   ```bash
   docker-compose up -d
   ```
3. Access the API at `http://localhost:8000`
   - OpenAPI docs: `http://localhost:8000/docs`

## Endpoints
- `POST /documents` → Create a document (title, content).
- `POST /documents/search` → Body: `{ "query": "...", "user_id": "<optional>" }`
- Runs cosine similarity and returns top 3 hits (requires documents to have embeddings).

## Precomputing embeddings
- Run the celery worker (automatically via compose `worker` service).
- To trigger precompute manually:
This enqueues a task which finds up to `limit` docs without embeddings and computes them.

## Embeddings provider
- If `OPENAI_API_KEY` is set in `.env`, the app will call OpenAI embeddings (model in `EMBEDDING_MODEL`).
- If not set, the app uses a deterministic pseudo-random vector (dev/test only). **Do not use fallback in production.**

## GDPR & Audit
- We never store raw user ID or PII.
- We store `hashed_user_id` = HMAC_SHA256(HMAC_KEY, user_id). Set a secure `HMAC_KEY`.
- Audit rows contain: `hashed_user_id`, `action`, `metadata`, `timestamp`.

## Design decisions (short)
- **Async FastAPI + SQLAlchemy async** for high concurrency and non-blocking DB calls.
- **pgvector** for efficient vector storage & operator support (`<#>` for cosine distance).
- **Celery** for embedding precomputation — decouples expensive network calls from request path.
- **HMAC hashing** of user ID to be GDPR-friendly (irreversible if HMAC key is secret).
- **Pluggable embedding provider** (OpenAI or local fallback) to keep module testable offline.

## Scalability Plan (concise)
- **Database**: use connection pooling; vertical scale first, then read replicas. Index on vector column with IVF/PGVector indexes (`CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);`).
- **Vector Best Practice**: create ivfflat index for fast ANN retrieval once you have >10k rows. Tune `lists`.
- **Worker**: run multiple Celery workers; use autoscaling or Kubernetes Jobs for batching embedding tasks.
- **Search Tier**: consider a specialized ANN store (Milvus, FAISS, Weaviate) for millions of documents; keep Postgres for transactional data + audit logs.
- **Security & GDPR**: rotate HMAC keys, rotate any API keys, keep audit logs immutable or export to long-term cold storage.
- **Monitoring**: Prometheus + Grafana, Sentry for exceptions, and task queue observability.


## To push to GitHub
1. `git init`
2. `git add . && git commit -m "Initial PHARMORIS backend"`
3. Create a new repo on GitHub and follow the `git remote add` / `git push` steps.
