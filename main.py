import logging
import os
import asyncio
import time
from fastapi import FastAPI, Request
from sqlalchemy import text
from api import router
from app.db.initdb import engine, Base
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware import MetricsMiddleware, RateLimitMiddleware, ErrorHandlingMiddleware
from app.core.metrics import metrics_router
from app.core.health import router as health_router

load_dotenv()
app = FastAPI(
    title="PHARMORIS Backend",
    version="1.0.0",
    description="""
    Advanced document search service with vector similarity search.
    Features:
    - FastAPI for high performance
    - pgvector for efficient similarity search
    - GDPR-compliant audit logging
    - Prometheus metrics
    - Health monitoring
    """,
    debug=True,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logger = logging.getLogger()
logger.setLevel(log_level)

formatter = logging.Formatter(
    "%(asctime)s - %(threadName)s %(filename)s:%(lineno)d - %(funcName)s() - %(levelname)s - %(message)s"
)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Add middleware in correct order
app.add_middleware(ErrorHandlingMiddleware)  # First to catch all errors
app.add_middleware(MetricsMiddleware)        # Then collect metrics
app.add_middleware(RateLimitMiddleware, requests_per_minute=int(os.getenv("RATE_LIMIT", "60")))
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(metrics_router, prefix="/metrics", tags=["monitoring"])
app.include_router(health_router, prefix="/health", tags=["monitoring"])

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log incoming requests and response times."""
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(f"Request completed: {request.method} {request.url} - {response.status_code} ({duration:.2f}s)")
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Request failed: {request.method} {request.url} - ({duration:.2f}s) - Error: {str(e)}")
        raise

    process_time = (time.time() - start_time) * 1000
    formatted_time = f"{process_time:.2f} ms"
    logger.info(f"Completed {request.method} {request.url} in {formatted_time}")
    return response


@app.on_event("startup")
async def startup():
    from app.db.initdb import init_db
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on application shutdown."""
    try:
        if engine:
            await engine.dispose()
            logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")