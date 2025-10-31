from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter
from starlette.responses import Response

metrics_router = APIRouter()

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests count',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# Search metrics
SEARCH_REQUESTS = Counter(
    'search_requests_total',
    'Total search requests',
    ['status']
)

SEARCH_LATENCY = Histogram(
    'search_latency_seconds',
    'Search request latency'
)

# Document metrics
DOCUMENT_COUNT = Counter(
    'documents_total',
    'Total number of documents',
    ['status']
)

EMBEDDING_COMPUTATION = Histogram(
    'embedding_computation_seconds',
    'Time taken to compute embeddings'
)

# Cache metrics
CACHE_HITS = Counter(
    'cache_hits_total',
    'Total number of cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'cache_misses_total',
    'Total number of cache misses',
    ['cache_type']
)

@metrics_router.get("/metrics")
async def metrics():
    """Endpoint to expose Prometheus metrics."""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )