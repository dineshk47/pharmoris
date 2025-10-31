from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
from pydantic import BaseModel
import os
from app.db.initdb import engine
from app.utils.backfill import update_document_embeddings

router = APIRouter(prefix="/admin", tags=["admin"])

# API key security
API_KEY_NAME = os.getenv("API_KEY_NAME", "X-API-Key")  # Default to X-API-Key if not set
API_KEY = os.getenv("API_KEY")
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    """Validate API key from header."""
    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="API key authentication not configured"
        )
    if api_key_header != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return api_key_header

class BackfillResponse(BaseModel):
    """Response model for backfill operation."""
    success_count: int
    failed_ids: list[int]
    message: str

@router.post("/fill-embeddings", response_model=BackfillResponse)
async def fill_embeddings(
    limit: Optional[int] = None,
    batch_size: Optional[int] = 10,
    api_key: str = Depends(get_api_key)
):
    """Fill missing embeddings for documents.
    
    Args:
        limit: Optional maximum number of documents to process
        batch_size: How many documents to process per batch
    
    Returns:
        BackfillResponse with success count and any failed document IDs
    """
    async with engine.begin() as conn:
        success_count, failed_ids = await update_document_embeddings(
            conn=conn,
            batch_size=batch_size,
            limit=limit
        )
    
    message = f"Processed {success_count + len(failed_ids)} documents. "
    message += f"{success_count} succeeded, {len(failed_ids)} failed."
    if failed_ids:
        message += f" Failed IDs: {failed_ids}"
    
    return BackfillResponse(
        success_count=success_count,
        failed_ids=failed_ids,
        message=message
    )