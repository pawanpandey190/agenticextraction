"""API routers."""

from app.routers.sessions import router as sessions_router
from app.routers.documents import router as documents_router
from app.routers.processing import router as processing_router

__all__ = ["sessions_router", "documents_router", "processing_router"]
