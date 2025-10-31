from fastapi import APIRouter
from app.documents.router import router as documents_router
from app.admin.router import router as admin_router

router = APIRouter()

router.include_router(
    documents_router,
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

router.include_router(
    admin_router,
    responses={
        401: {"description": "Invalid API key"},
        503: {"description": "API key not configured"}
    },
)
