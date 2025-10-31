from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

async def http_exception_handler(request: Request, exc: HTTPException):
    logging.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": exc.status_code,
            "path": request.url.path
        }
    )