"""Processing and progress endpoints."""

import json
from fastapi import APIRouter, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.models.api_models import ProcessRequest, ManualLetterRequest
from app.models.session import SessionStatus
from app.services.session_manager import session_manager
from app.services.file_handler import file_handler
from app.services.orchestrator_runner import orchestrator_runner

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["processing"])


@router.post("/process", status_code=status.HTTP_202_ACCEPTED)
async def start_processing(session_id: str, request: ProcessRequest = ProcessRequest()):
    """Start processing documents in a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if session.status == SessionStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is already processing",
        )

    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has already completed processing",
        )

    # Check if there are files to process
    files = file_handler.list_uploaded_files(session_id)
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded to process",
        )

    # Update session status
    session.update_status(SessionStatus.PROCESSING)
    session_manager.update_session(session)

    # TRIGGER BACKGROUND TASK IMMEDIATELY (Eager Processing)
    # This ensures the task starts even if no one is watching /progress yet.
    # The global semaphore in OrchestratorRunner will ensure they run sequentially.
    await orchestrator_runner.start_background_task(session_id)

    return {
        "message": "Processing started",
        "session_id": session_id,
        "progress_url": f"/api/sessions/{session_id}/progress",
    }


@router.post("/cancel", status_code=status.HTTP_200_OK)
async def cancel_processing(session_id: str):
    """Cancel processing for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED):
        return {
            "message": f"Session already in terminal state: {session.status}",
            "session_id": session_id,
        }

    if session.status not in (SessionStatus.PROCESSING, SessionStatus.UPLOADING, SessionStatus.CREATED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel session in status: {session.status}",
        )

    # Cancel the orchestrator task
    cancelled = await orchestrator_runner.cancel_session(session_id)
    
    if cancelled:
        # Update session status
        session.update_status(SessionStatus.FAILED)
        session.error_message = "Processing cancelled by user"
        session_manager.update_session(session)
        
        return {
            "message": "Processing cancelled",
            "session_id": session_id,
        }
    else:
        return {
            "message": "No active processing found for this session",
            "session_id": session_id,
        }


@router.get("/progress")
async def get_progress(session_id: str):
    """Get progress updates via Server-Sent Events (SSE)."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    async def event_generator():
        """Generate SSE events from orchestrator progress."""
        async for event in orchestrator_runner.run_with_progress(session_id):
            yield {
                "event": "progress",
                "data": event.model_dump_json(),
            }

            # If completed or error, close the stream
            if event.completed or event.error:
                break

    return EventSourceResponse(event_generator())


@router.get("/result")
async def get_result(session_id: str):
    """Get the analysis result."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if not session.result_available:
        if session.status == SessionStatus.PROCESSING:
            raise HTTPException(
                status_code=status.HTTP_202_ACCEPTED,
                detail="Processing in progress",
            )
        elif session.status == SessionStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=session.error_message or "Processing failed",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Processing not started",
            )

    # Read and return the result
    file_path = file_handler.get_result_file(session_id, "analysis_result.json")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result file not found",
        )

    with open(file_path) as f:
        result = json.load(f)

    return result

@router.post("/generate-letter")
async def generate_manual_letter(session_id: str, request: ManualLetterRequest):
    """Manually generate admission letter with overrides."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    # Get baseline data from results if available
    student_data = {}
    result_path = file_handler.get_result_file(session_id, "analysis_result.json")
    if result_path and result_path.exists():
        with open(result_path) as f:
            student_data = json.load(f)

    # Generate output path
    output_dir = session_manager.get_output_dir(session_id)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"admission_letter_{session_id}.docx"

    from app.services.letter_service import letter_service
    
    success_path = letter_service.generate_admission_letter(
        student_data=student_data,
        output_path=output_path,
        override_name=request.student_name,
        override_date=request.date
    )

    if not success_path:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate manual letter",
        )

    # Update session flag
    session.letter_available = True
    session_manager.update_session(session)

    return {
        "message": "Manual letter generated successfully",
        "download_url": f"/api/sessions/{session_id}/download/letter"
    }
