from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict
import asyncio
import logging
from .metrics import REQUEST_COUNT, REQUEST_LATENCY

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
    async def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] if req_time > minute_ago]
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return False
            
        self.requests[client_ip].append(now)
        return True
    
    async def _periodic_cleanup(self):
        while True:
            await asyncio.sleep(60)
            now = time.time()
            minute_ago = now - 60
            for ip in list(self.requests.keys()):
                self.requests[ip] = [req_time for req_time in self.requests[ip] if req_time > minute_ago]
                if not self.requests[ip]:
                    del self.requests[ip]

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)
            
            return response
            
        except Exception as e:
            logging.error(f"Request failed: {str(e)}")
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=500
            ).inc()
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        
        if not await self.limiter.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": "60 seconds"
                }
            )
        
        return await call_next(request)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as e:
            raise
        except Exception as e:
            logging.error(f"Unhandled error: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_id": str(time.time())
                }
            )