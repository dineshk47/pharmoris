from fastapi import APIRouter
from app.documents.router import router as documents_router

router = APIRouter()

router.include_router(
    documents_router,
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)
