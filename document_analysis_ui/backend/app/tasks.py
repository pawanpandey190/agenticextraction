"""Celery tasks for document analysis."""

import os
import sys
import json
from pathlib import Path
import structlog
from app.celery_app import celery_app
from app.config import settings
from app.services.session_manager import session_manager
from app.models.session import SessionStatus
from app.services.letter_service import letter_service

logger = structlog.get_logger(__name__)

@celery_app.task(bind=True)
def run_analysis_task(self, session_id: str):
    """Run master orchestrator analysis for a session."""
    logger.info("celery_task_started", session_id=session_id, task_id=self.request.id)
    
    # 1. Get session info
    session = session_manager.get_session(session_id)
    if not session:
        logger.error("session_not_found", session_id=session_id)
        return {"status": "error", "message": "Session not found"}

    upload_dir = session_manager.get_upload_dir(session_id)
    output_dir = session_manager.get_output_dir(session_id)
    
    # 2. Update status
    session.update_status(SessionStatus.PROCESSING)
    session_manager.update_session(session)

    # 3. Setup paths for orchestrator (similar to OrchestratorRunner)
    backend_root = Path(__file__).parent.parent
    orchestrator_base = backend_root.parent / "master_orchestrator_agent"
    
    # Add agent paths to sys.path
    agent_paths = [
        orchestrator_base / "src",
        orchestrator_base.parent / "passport_analysis_agent" / "src",
        orchestrator_base.parent / "education_credential_agent" / "src",
        orchestrator_base.parent / "financial_document_agent" / "src",
    ]
    
    for path in agent_paths:
        if path.exists():
            str_path = str(path)
            if str_path not in sys.path:
                sys.path.insert(0, str_path)

    # 4. Define progress callback
    import redis
    redis_client = redis.from_url(settings.redis_url)

    def progress_callback(update):
        """Update session progress and publish to Redis."""
        # Update session on disk (as before)
        s = session_manager.get_session(session_id)
        if s:
            s.current_document = update.current_document
            s.processed_documents = update.processed_documents
            s.total_documents = update.total_documents
            # Calculate percentage (0-100)
            percentage = ((update.stage_index + 1) / update.total_stages) * 100
            s.progress_percentage = percentage
            session_manager.update_session(s)
            
            # Publish to Redis for real-time UI updates
            try:
                from app.models.progress import ProgressEvent, ProgressUpdate as PydanticProgressUpdate
                
                # Convert dataclass to Pydantic model for serialization
                event = ProgressEvent.from_update(PydanticProgressUpdate(
                    stage_name=update.stage_name,
                    stage_index=update.stage_index,
                    total_stages=update.total_stages,
                    sub_agent=update.sub_agent,
                    sub_stage_name=update.sub_stage_name,
                    sub_stage_index=update.sub_stage_index,
                    sub_total_stages=update.sub_total_stages,
                    message=update.message,
                    current_document=update.current_document,
                    processed_documents=update.processed_documents,
                    total_documents=update.total_documents
                ))
                
                channel = f"session_progress:{session_id}"
                redis_client.publish(channel, event.model_dump_json())
            except Exception as e:
                logger.error("redis_publish_error", error=str(e))

    # 5. Execute orchestrator
    try:
        from master_orchestrator.pipeline.orchestrator import MasterOrchestrator
        from master_orchestrator.config.constants import OutputFormat

        orchestrator = MasterOrchestrator(progress_callback=progress_callback)
        orchestrator.process(
            input_folder=upload_dir,
            output_dir=output_dir,
            output_format=OutputFormat.BOTH,
            bank_statement_months=session.bank_statement_period,
            financial_threshold=session.financial_threshold,
        )

        # 6. Post-processing (Letter generation)
        output_file = output_dir / "analysis_result.json"
        if output_file.exists():
            with open(output_file) as f:
                analysis_data = json.load(f)
            
            # Update student name and letter availability
            s = session_manager.get_session(session_id)
            if s:
                # Name extraction logic
                passport = analysis_data.get("passport_details", {})
                first_name = passport.get("first_name")
                last_name = passport.get("last_name")
                if first_name and last_name:
                    extracted_name = f"{first_name} {last_name}"
                    s.student_name = session_manager.resolve_duplicate_name(extracted_name, session_id)
                
                # Letter generation
                accuracy = passport.get("accuracy_score", 0)
                if accuracy >= 70:
                    letter_path = output_dir / f"admission_letter_{session_id}.docx"
                    if letter_service.generate_admission_letter(analysis_data, letter_path):
                        s.letter_available = True
                
                s.result_available = True
                s.update_status(SessionStatus.COMPLETED)
                session_manager.update_session(s)
                logger.info("celery_task_completed", session_id=session_id)
        else:
            raise Exception("Output file not generated")

    except Exception as e:
        logger.error("celery_task_failed", session_id=session_id, error=str(e))
        s = session_manager.get_session(session_id)
        if s:
            s.update_status(SessionStatus.FAILED)
            s.error_message = str(e)
            session_manager.update_session(s)
        return {"status": "error", "message": str(e)}

    return {"status": "success", "session_id": session_id}
