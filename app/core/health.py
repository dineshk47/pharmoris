from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db.initdb import engine
from app.utils.embeddings import get_embedding
import redis
import time
import logging

router = APIRouter()

async def check_database():
    """Check database connectivity and pgvector extension."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.execute(text("SELECT 'test'::vector"))
            return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        logging.error(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

async def check_redis():
    """Check Redis connectivity."""
    try:
        redis_url = "redis://localhost:6379"
        r = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        r.ping()
        return {"status": "healthy", "latency_ms": 0}
    except Exception as e:
        logging.error(f"Redis health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

async def check_embedding_service():
    """Check embedding service."""
    try:
        start_time = time.time()
        await get_embedding("test")
        latency = (time.time() - start_time) * 1000
        return {"status": "healthy", "latency_ms": round(latency, 2)}
    except Exception as e:
        logging.error(f"Embedding service health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    Returns detailed status of all system components.
    """
    results = {
        "database": await check_database(),
        "redis": await check_redis(),
        "embedding_service": await check_embedding_service(),
    }
    
    overall_status = all(v["status"] == "healthy" for v in results.values())
    
    response = {
        "status": "healthy" if overall_status else "unhealthy",
        "timestamp": time.time(),
        "components": results
    }
    
    if not overall_status:
        raise HTTPException(status_code=503, detail=response)
        
    return response

@router.get("/health/live")
async def liveness():
    """Quick liveness check."""
    return {"status": "alive", "timestamp": time.time()}