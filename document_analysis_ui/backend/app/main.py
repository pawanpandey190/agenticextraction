"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import sessions_router, documents_router, processing_router
from app.routers.documents import batch_router
from app.services.session_manager import session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup: schedule periodic cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    yield

    # Shutdown: cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


async def periodic_cleanup():
    """Periodically clean up expired sessions."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            session_manager.cleanup_expired_sessions()
        except asyncio.CancelledError:
            break
        except Exception:
            pass  # Continue on error


app = FastAPI(
    title="Document Analysis UI",
    description="Web UI for Document Analysis Agents",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions_router)
app.include_router(documents_router)
app.include_router(processing_router)
app.include_router(batch_router)  # Batch upload router


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Document Analysis UI API",
        "version": "0.1.0",
        "docs_url": "/docs",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
