import os
from celery import Celery
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from ..db.initdb import AsyncSessionLocal
from app.documents.models import Document
from .embeddings import get_embedding

CELERY_BROKER = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER)

celery = Celery("worker", broker=CELERY_BROKER, backend=CELERY_BACKEND)

@celery.task(bind=True)
def precompute_embeddings(self, limit=100):
    # Celery is sync; we run asyncio inside it to access async DB
    asyncio.run(_precompute(limit))

async def _precompute(limit=100):
    async with AsyncSessionLocal() as session:
        q = select(Document).where(Document.embedding.is_(None)).limit(limit)
        result = await session.execute(q)
        docs = result.scalars().all()
        for d in docs:
            emb = await get_embedding(d.content)
            # use raw UPDATE with engine to ensure vector is stored correctly:
            # SQLAlchemy supports setting Vector via column assignment
            d.embedding = emb
            session.add(d)
        await session.commit()
