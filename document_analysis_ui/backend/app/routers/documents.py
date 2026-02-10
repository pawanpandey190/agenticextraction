"""Document upload endpoints."""

from fastapi import APIRouter, File, HTTPException, UploadFile, status, Query
from fastapi.responses import FileResponse

from app.models.api_models import UploadResponse, BatchUploadResponse, BatchSessionInfo
from app.models.session import SessionStatus
from app.services.file_handler import file_handler
from app.services.session_manager import session_manager
from app.services.batch_manager import batch_manager

router = APIRouter(prefix="/api/sessions/{session_id}", tags=["documents"])


@router.post("/documents", response_model=UploadResponse)
async def upload_documents(
    session_id: str,
    files: list[UploadFile] = File(...),
):
    """Upload documents to a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if session.status not in (SessionStatus.CREATED, SessionStatus.UPLOADING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload files to session in status: {session.status}",
        )

    uploaded_files = []
    errors = []

    for file in files:
        try:
            content = await file.read()
            await file_handler.save_uploaded_file(
                session_id=session_id,
                filename=file.filename or "unknown",
                content=content,
            )
            uploaded_files.append(file.filename or "unknown")
        except ValueError as e:
            errors.append(f"{file.filename}: {str(e)}")
        except Exception as e:
            errors.append(f"{file.filename}: Upload failed - {str(e)}")

    if errors and not uploaded_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(errors),
        )

    # Update session
    session.uploaded_files = file_handler.list_uploaded_files(session_id)
    session.total_files = len(session.uploaded_files)
    session.update_status(SessionStatus.UPLOADING)
    session_manager.update_session(session)

    return UploadResponse(
        uploaded_files=uploaded_files,
        total_files=session.total_files,
    )


@router.get("/documents")
async def list_documents(session_id: str):
    """List uploaded documents for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    files = file_handler.list_uploaded_files(session_id)
    return {"files": files, "total": len(files)}


@router.delete("/documents/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(session_id: str, filename: str):
    """Delete an uploaded document."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if session.status not in (SessionStatus.CREATED, SessionStatus.UPLOADING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete files from session in status: {session.status}",
        )

    if not file_handler.delete_file(session_id, filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filename}",
        )

    # Update session
    session.uploaded_files = file_handler.list_uploaded_files(session_id)
    session.total_files = len(session.uploaded_files)
    session_manager.update_session(session)


@router.get("/download/json")
async def download_json(session_id: str):
    """Download the analysis result as JSON."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if not session.result_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Results not available yet",
        )

    file_path = file_handler.get_result_file(session_id, "analysis_result.json")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JSON result file not found",
        )

    return FileResponse(
        path=file_path,
        filename="analysis_result.json",
        media_type="application/json",
    )


@router.get("/download/excel")
async def download_excel(session_id: str):
    """Download the analysis result as Excel."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if not session.result_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Results not available yet",
        )

    file_path = file_handler.get_result_file(session_id, "analysis_result.xlsx")
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Excel result file not found",
        )

    return FileResponse(
        path=file_path,
        filename="analysis_result.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.get("/download/letter")
async def download_letter(session_id: str):
    """Download the generated admission letter as Word Document."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    if not session.letter_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admission letter not available for this session",
        )

    # Generated letters are in the output directory
    output_dir = session_manager.get_output_dir(session_id)
    letter_path = output_dir / f"admission_letter_{session_id}.docx"
    
    if not letter_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Letter file not found on disk",
        )

    return FileResponse(
        path=letter_path,
        filename=f"Admission_Letter_{session.student_name or session_id}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


# Batch Upload Endpoints

batch_router = APIRouter(prefix="/api/batches", tags=["batch"])


@batch_router.post("/upload", response_model=BatchUploadResponse)
async def upload_batch_folders(
    files: list[UploadFile] = File(...),
    financial_threshold: float = Query(default=15000.0),
    bank_statement_period: int = Query(default=3),
):
    """Upload multiple student folders in batch.
    
    Supports both:
    - Multiple folders (student_name/documents)
    - Single student folder (just documents)
    """
    # Read all files
    file_data = []
    for file in files:
        content = await file.read()
        # Preserve folder structure in filename
        filename = file.filename or "unknown"
        file_data.append((filename, content))

    # Extract student folders
    student_folders = file_handler.extract_student_folders(file_data)

    # Validate each student folder
    invalid_students = []
    for student_name, student_files in student_folders.items():
        is_valid, error_msg = file_handler.validate_student_folder(student_files)
        if not is_valid:
            invalid_students.append(f"{student_name}: {error_msg}")

    if invalid_students:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid student folders: {'; '.join(invalid_students)}",
        )

    # Create batch
    batch = batch_manager.create_batch([])  # Will update with session IDs

    # Create sessions for each student
    sessions = session_manager.create_batch_sessions(
        student_folders={name: [] for name in student_folders.keys()},
        batch_id=batch.batch_id,
        financial_threshold=financial_threshold,
        bank_statement_period=bank_statement_period,
    )

    # Upload files to each session
    session_infos = []
    for session in sessions:
        student_name = session.student_name or "Unknown"
        student_files = student_folders.get(student_name, [])

        # Upload files for this student
        for filename, content in student_files:
            try:
                await file_handler.save_uploaded_file(
                    session_id=session.id,
                    filename=filename,
                    content=content,
                )
            except Exception as e:
                # Log error but continue
                pass

        # Update session file list
        session.uploaded_files = file_handler.list_uploaded_files(session.id)
        session.total_files = len(session.uploaded_files)
        
        # TRIGGER PROCESSING IMMEDIATELY
        from app.services.orchestrator_runner import orchestrator_runner
        session.update_status(SessionStatus.PROCESSING)
        session_manager.update_session(session)
        await orchestrator_runner.start_background_task(session.id)

        session_infos.append(
            BatchSessionInfo(
                session_id=session.id,
                student_name=student_name,
                status=session.status,
                total_files=session.total_files,
                result_available=False,
            )
        )

    # Update batch with session IDs
    batch.student_sessions = [s.id for s in sessions]

    return BatchUploadResponse(
        batch_id=batch.batch_id,
        total_students=len(sessions),
        sessions=session_infos,
        message=f"Successfully uploaded {len(sessions)} student folder(s)",
    )


@router.get("/documents/{filename}/view")
async def view_document(session_id: str, filename: str):
    """Serve a document for viewing in the browser."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    file_path = file_handler.get_document_path(session_id, filename)
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {filename}",
        )

    # Determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@router.get("/documents/list")
async def list_session_documents(session_id: str):
    """Get list of all uploaded documents for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {session_id}",
        )

    documents = file_handler.get_uploaded_documents(session_id)
    return {"documents": documents, "total": len(documents)}
