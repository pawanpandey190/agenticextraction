"""Session management endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.models.api_models import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionResponse,
    BatchStatusResponse,
)
from app.models.session import SessionStatus
from app.services.session_manager import session_manager
from app.services.batch_manager import batch_manager

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=CreateSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest = CreateSessionRequest()):
    """Create a new processing session."""
    session = session_manager.create_session(
        financial_threshold=request.financial_threshold,
        bank_statement_period=request.bank_statement_period
    )
    return CreateSessionResponse(
        session_id=session.id,
        status=session.status,
        upload_url=f"/api/sessions/{session.id}/documents",
    )


@router.get("", response_model=list[SessionResponse])
async def list_sessions():
    """List all sessions."""
    sessions = session_manager.list_sessions()
    return [
        SessionResponse(
            id=s.id,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
            uploaded_files=s.uploaded_files,
            total_files=s.total_files,
            financial_threshold=s.financial_threshold,
            bank_statement_period=s.bank_statement_period,
            result_available=s.result_available,
            letter_available=s.letter_available,
            error_message=s.error_message,
            batch_id=s.batch_id,
            student_name=s.student_name,
            current_document=s.current_document,
            processed_documents=s.processed_documents,
            total_documents=s.total_documents,
            progress_percentage=s.progress_percentage,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a session by ID."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )
    return SessionResponse(
        id=session.id,
        status=session.status,
        created_at=session.created_at,
        updated_at=session.updated_at,
        uploaded_files=session.uploaded_files,
        total_files=session.total_files,
        financial_threshold=session.financial_threshold,
        bank_statement_period=session.bank_statement_period,
        result_available=session.result_available,
        letter_available=session.letter_available,
        error_message=session.error_message,
        batch_id=session.batch_id,
        student_name=session.student_name,
        current_document=session.current_document,
        processed_documents=session.processed_documents,
        total_documents=session.total_documents,
        progress_percentage=session.progress_percentage,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """Delete a session and all its files."""
    if not session_manager.delete_session(session_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )


@router.post("/cleanup")
async def cleanup_sessions():
    """Clean up expired sessions."""
    cleaned = session_manager.cleanup_expired_sessions()
    return {"cleaned": cleaned}


# Batch endpoints

@router.get("/batches/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """Get status of a batch upload."""
    batch = batch_manager.get_batch(batch_id)
    
    # Get all sessions in the batch
    sessions = session_manager.get_sessions_by_batch(batch_id)
    
    if not batch:
        if sessions:
            # Reconstruct batch from sessions found on disk
            batch = batch_manager.reconstruct_batch(
                batch_id, 
                [s.id for s in sessions]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch not found: {batch_id}",
            )

    # Get detailed status
    batch_status = batch_manager.get_batch_status(batch_id, sessions)
    if not batch_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}",
        )

    return batch_status


@router.get("/batches/{batch_id}/sessions", response_model=list[SessionResponse])
async def get_batch_sessions(batch_id: str):
    """Get all sessions in a batch."""
    batch = batch_manager.get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}",
        )

    sessions = session_manager.get_sessions_by_batch(batch_id)
    return [
        SessionResponse(
            id=s.id,
            status=s.status,
            created_at=s.created_at,
            updated_at=s.updated_at,
            uploaded_files=s.uploaded_files,
            total_files=s.total_files,
            financial_threshold=s.financial_threshold,
            bank_statement_period=s.bank_statement_period,
            result_available=s.result_available,
            letter_available=s.letter_available,
            error_message=s.error_message,
            batch_id=s.batch_id,
            student_name=s.student_name,
            current_document=s.current_document,
            processed_documents=s.processed_documents,
            total_documents=s.total_documents,
            progress_percentage=s.progress_percentage,
        )
        for s in sessions
    ]
