import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import json

logger = logging.getLogger("pharmoris_backend")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        try:
            body = await request.json()
        except Exception:
            body = None
        logger.info(f"Incoming {request.method} {request.url.path} body={json.dumps(body) if body else None}")
        response = await call_next(request)
        duration = (time.time() - start) * 1000
        logger.info(f"Response {request.method} {request.url.path} status_code={response.status_code} duration_ms={duration:.2f}")
        return response
