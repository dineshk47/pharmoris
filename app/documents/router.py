from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.initdb import get_session
from app.documents.schemas import DocumentCreate, DocumentOut, SearchRequest, SearchResponse
from app.documents.service import DocumentService

router = APIRouter()

@router.post("/documents", response_model=DocumentOut)
async def create_document(
    payload: DocumentCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new document.
    
    The document's embedding will be computed either immediately or in the background.
    """
    service = DocumentService(session)
    return await service.create_document(payload)

@router.post("/documents/search", response_model=SearchResponse)
async def search_documents(
    req: SearchRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Search for documents using vector similarity.
    
    The search will use:
    1. Vector similarity if embeddings are available
    2. Fallback to text search if vector search fails
    """
    service = DocumentService(session)
    return await service.search_documents(req)
