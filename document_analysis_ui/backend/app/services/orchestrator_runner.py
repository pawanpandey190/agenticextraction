"""Wrapper for running the Master Orchestrator with progress callbacks."""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import AsyncGenerator, Callable

import structlog
from dotenv import load_dotenv

from app.config import settings
from app.models.progress import ProgressEvent, ProgressUpdate
from app.models.session import SessionStatus
from app.services.session_manager import session_manager
from app.services.letter_service import letter_service

logger = structlog.get_logger(__name__)

# Type alias for progress callback
ProgressCallback = Callable[[ProgressUpdate], None]

# Expected output filename from orchestrator
OUTPUT_FILENAME = "analysis_result.json"


class OrchestratorRunner:
    """Runs the Master Orchestrator with progress tracking."""

    def __init__(self):
        """Initialize the orchestrator runner."""
        # Path to master orchestrator
        # Path: services/ -> app/ -> backend/ -> document_analysis_ui/ -> claude_agents/
        orchestrator_base = Path(__file__).parent.parent.parent.parent.parent / "master_orchestrator_agent"
        orchestrator_path = orchestrator_base / "src"

        # Load .env from master_orchestrator_agent directory
        env_file = orchestrator_base / ".env"
        # Also check root directory (one level up from orchestrator_base)
        root_env = orchestrator_base.parent / ".env"
        
        if root_env.exists():
            from dotenv import load_dotenv
            load_dotenv(root_env, override=True)
            # Proactively strip all loaded keys
            for k, v in os.environ.items():
                if "ANTHROPIC_API_KEY" in k or "OPENAI_API_KEY" in k:
                    os.environ[k] = v.strip().strip('"').strip("'")
            
            logger.error("ROOT_ENV_LOADED", env_file=str(root_env))
            # Critical diagnostic
            key = os.environ.get("ANTHROPIC_API_KEY", "MISSING")
            key_preview = f"{key[:12]}...{key[-5:]}" if key != "MISSING" else "MISSING"
            logger.error("ENV_CHECK", key_preview=key_preview, key_len=len(key) if key != "MISSING" else 0)
        
        if env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            logger.error("ORCHESTRATOR_ENV_LOADED", env_file=str(env_file))
        
        if not root_env.exists() and not env_file.exists():
            logger.warning("no_env_file_found", searched=[str(root_env), str(env_file)])

        # Add all agents to path to ensure local changes take precedence
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
                logger.error("ADDED_TO_SYS_PATH", path=str_path)
            else:
                logger.warning("agent_path_not_found", path=str(path))

        # CRITICAL DIAGNOSTIC
        try:
            import passport_agent
            import education_agent
            import financial_agent
            logger.error("MODULE_LOAD_DIAGNOSTIC", 
                         passport=passport_agent.__file__,
                         education=education_agent.__file__,
                         financial=financial_agent.__file__)
        except Exception as e:
            logger.error("MODULE_LOAD_ERROR", error=str(e))

        # Track progress queues per session
        self._progress_queues: dict[str, list[asyncio.Queue]] = {}
        self._task_locks: dict[str, asyncio.Lock] = {}
        self._redis_listeners: dict[str, asyncio.Task] = {}

    def _get_lock(self, session_id: str) -> asyncio.Lock:
        """Get or create a lock for a specific session.
        This dictionary access is atomic in CPython's GIL.
        """
        return self._task_locks.setdefault(session_id, asyncio.Lock())

    async def cancel_session(self, session_id: str) -> bool:
        """Cancel processing for a session using Celery revoke."""
        session = session_manager.get_session(session_id)
        if session and session.celery_task_id:
            logger.info("revoking_celery_task", session_id=session_id, task_id=session.celery_task_id)
            from app.celery_app import celery_app
            celery_app.control.revoke(session.celery_task_id, terminate=True, signal='SIGKILL')
            
            # Clean up tracking
            async with self._get_lock(session_id):
                queues = self._progress_queues.pop(session_id, None)
                if queues:
                    for q in queues:
                        try:
                            q.put_nowait(None)
                        except: pass
            
            return True
        
        logger.warning("no_celery_task_to_cancel", session_id=session_id)
        return False

    async def run_with_progress(
        self,
        session_id: str,
    ) -> AsyncGenerator[ProgressEvent, None]:
        """Run the orchestrator and yield progress events.

        Args:
            session_id: Session identifier.

        Yields:
            ProgressEvent instances as processing progresses.
        """
        session = session_manager.get_session(session_id)
        if not session:
            yield ProgressEvent.error_event(f"Session not found: {session_id}")
            return

        # Check if session already completed or failed - don't restart
        if session.status == SessionStatus.COMPLETED:
            logger.info("session_already_completed", session_id=session_id)
            yield ProgressEvent.completed_event()
            return

        if session.status == SessionStatus.FAILED:
            logger.info("session_already_failed", session_id=session_id)
            yield ProgressEvent.error_event(session.error_message or "Processing failed")
            return

        upload_dir = session_manager.get_upload_dir(session_id)
        output_dir = session_manager.get_output_dir(session_id)

        # Ensure task is running
        orchestrator_task = await self.start_background_task(session_id)
        if not orchestrator_task:
            yield ProgressEvent.error_event("Failed to start processing task")
            return
            
        # Create a new personal queue for this subscriber
        personal_queue: asyncio.Queue[ProgressUpdate | None] = asyncio.Queue()
        async with self._get_lock(session_id):
            if session_id not in self._progress_queues:
                self._progress_queues[session_id] = []
            self._progress_queues[session_id].append(personal_queue)
            
            # Start Redis listener if not already running for this session
            if session_id not in self._redis_listeners:
                self._redis_listeners[session_id] = asyncio.create_task(
                    self._listen_to_redis_progress(session_id)
                )
        
        try:
            # Flow until complete (or timeout)
            async for event in self._stream_from_personal_queue(session_id, personal_queue):
                yield event
        finally:
            # Cleanup personal queue
            async with self._get_lock(session_id):
                if session_id in self._progress_queues:
                    if personal_queue in self._progress_queues[session_id]:
                        self._progress_queues[session_id].remove(personal_queue)
                    if not self._progress_queues[session_id]:
                        self._progress_queues.pop(session_id)

    async def _listen_to_redis_progress(self, session_id: str):
        """Listen to Redis Pub/Sub for progress updates from Celery workers."""
        import redis.asyncio as redis
        
        try:
            client = redis.from_url(settings.redis_url)
            pubsub = client.pubsub()
            channel = f"session_progress:{session_id}"
            await pubsub.subscribe(channel)
            
            logger.info("redis_subscription_started", session_id=session_id)
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        update = ProgressUpdate(**data)
                        
                        # Update session in SessionManager cache immediately
                        session = session_manager.get_session(session_id)
                        if session:
                            session.current_document = update.current_document
                            session.processed_documents = update.processed_documents
                            session.total_documents = update.total_documents
                            percentage = ((update.stage_index + 1) / update.total_stages) * 100
                            session.progress_percentage = percentage
                            # We don't need to save to disk here, the worker already did
                            # But we ensure our local cache reflects it
                            session_manager.update_session(session)

                        # Broadcast to all queues for this session
                        async with self._get_lock(session_id):
                            queues = self._progress_queues.get(session_id, [])
                            for q in queues:
                                q.put_nowait(update)
                    except Exception as e:
                        logger.error("redis_message_parse_error", error=str(e))
                
                # Check if session is finished to stop listening
                session = session_manager.get_session(session_id)
                if session and session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED):
                    break
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error("redis_listener_error", error=str(e), session_id=session_id)
        finally:
            # Clean up
            async with self._get_lock(session_id):
                self._redis_listeners.pop(session_id, None)
                # Send completion signal to ALL queues so they don't wait forever
                queues = self._progress_queues.get(session_id, [])
                for q in queues:
                    try:
                        q.put_nowait(None)
                    except: pass

    async def _stream_from_personal_queue(
        self,
        session_id: str,
        personal_queue: asyncio.Queue,
    ) -> AsyncGenerator[ProgressEvent, None]:
        """Stream progress events from a personal queue."""
        try:
            while True:
                try:
                    update = await asyncio.wait_for(personal_queue.get(), timeout=1.0)
                    if update is None:
                        break
                    yield ProgressEvent.from_update(update)
                except asyncio.TimeoutError:
                    # Check if session is in terminal state
                    session = session_manager.get_session(session_id)
                    if session and session.status in (SessionStatus.COMPLETED, SessionStatus.FAILED):
                        # Final drain
                        while not personal_queue.empty():
                            update = personal_queue.get_nowait()
                            if update: yield ProgressEvent.from_update(update)
                        break
                    continue
            
            # Final check of status
            session = session_manager.get_session(session_id)
            if session and session.status == SessionStatus.COMPLETED:
                yield ProgressEvent.completed_event()
            elif session and session.status == SessionStatus.FAILED:
                yield ProgressEvent.error_event(session.error_message or "Processing failed")
        except Exception as e:
            logger.error("stream_personal_queue_error", error=str(e), session_id=session_id)
            yield ProgressEvent.error_event(str(e))

    async def _stream_from_queue(self, *args, **kwargs):
        # OBSOLETE - Replaced by _stream_from_personal_queue
        pass

    async def start_background_task(self, session_id: str) -> str | None:
        """Start the orchestrator task in Celery."""
        async with self._get_lock(session_id):
            session = session_manager.get_session(session_id)
            if not session:
                return None

            # If already processing, just return existing id
            if session.status == SessionStatus.PROCESSING and session.celery_task_id:
                return session.celery_task_id

            # Dispatch to Celery
            from app.tasks import run_analysis_task
            result = run_analysis_task.delay(session_id)
            
            # Save task ID
            session.celery_task_id = result.id
            session.update_status(SessionStatus.PROCESSING)
            session_manager.update_session(session)
            
            logger.info("dispatched_to_celery", session_id=session_id, task_id=result.id)
            return result.id

    async def _run_orchestrator_work_wrapped(self, session_id: str, upload_dir: Path, output_dir: Path, progress_callback: ProgressCallback):
        """Internal wrapper to run orchestrator and handle completion/errors."""
        try:
            # Yield initial status if session manager supports it
            session = session_manager.get_session(session_id)
            if session:
                session.update_status(SessionStatus.PROCESSING)
                session_manager.update_session(session)

            await self._run_orchestrator_with_timeout(
                upload_dir, 
                output_dir, 
                progress_callback, 
                session_id,
                bank_statement_months=session.bank_statement_period,
                financial_threshold=session.financial_threshold
            )
            
            # Post-processing logic (moved from run_with_progress)
            output_file = output_dir / OUTPUT_FILENAME
            session = session_manager.get_session(session_id)
            if not session: return

            if output_file.exists():
                session.result_available = True
                
                # Letter generation (acc >= 70)
                try:
                    with open(output_file) as f:
                        analysis_data = json.load(f)
                    
                    # Update student name if missing
                    if not session.student_name:
                        # Try to find name in passport, then education, then financial
                        passport = analysis_data.get("passport_details", {})
                        first_name = passport.get("first_name")
                        last_name = passport.get("last_name")
                        
                        if first_name and last_name:
                            name = f"{first_name} {last_name}"
                        else:
                            name = first_name or last_name
                            
                        if name:
                            session.student_name = session_manager.resolve_duplicate_name(name, session_id)
                        else:
                            # Try education summary
                            edu = analysis_data.get("education_summary", {})
                            if edu.get("student_name"):
                                session.student_name = edu["student_name"]
                        
                        if session.student_name:
                            logger.info("extracted_student_name", session_id=session_id, name=session.student_name)

                    passport = analysis_data.get("passport_details", {})
                    accuracy = passport.get("accuracy_score", 0)
                    
                    if accuracy >= 70:
                        letter_path = output_dir / f"admission_letter_{session.id}.docx"
                        if letter_service.generate_admission_letter(analysis_data, letter_path):
                            session.letter_available = True
                except Exception as ex:
                    logger.error("post_processing_failed", session_id=session_id, error=str(ex))

                session.update_status(SessionStatus.COMPLETED)
                session_manager.update_session(session)
            else:
                session.update_status(SessionStatus.FAILED)
                session.error_message = "Output file not generated"
                session_manager.update_session(session)
                
        except asyncio.CancelledError:
            logger.info("task_cancelled", session_id=session_id)
            raise
        except Exception as e:
            logger.error("task_failed", session_id=session_id, error=str(e))
            session = session_manager.get_session(session_id)
            if session:
                session.update_status(SessionStatus.FAILED)
                session.error_message = str(e)
                session_manager.update_session(session)
        finally:
            # Send completion signal to ALL queues
            queues = self._progress_queues.get(session_id, [])
            for q in queues:
                await q.put(None)
            
            # Clean up task (but leave queues for final drain if needed, 
            # though run_with_progress handles it)
            async with self._get_lock(session_id):
                # We pop the task only if no one is listening, 
                # or we let listeners pop it. Actually, safest to pop it here.
                self._active_tasks.pop(session_id, None)

    async def _run_orchestrator_with_timeout(
        self,
        upload_dir: Path,
        output_dir: Path,
        progress_callback: ProgressCallback,
        session_id: str,
        bank_statement_months: int | None = None,
        financial_threshold: float | None = None,
    ):
        """Run orchestrator with timeout and retry logic.
        
        Args:
            upload_dir: Path to uploaded documents.
            output_dir: Path for output files.
            progress_callback: Callback for progress updates.
            session_id: Session identifier for logging.
            
        Returns:
            Orchestrator result.
            
        Raises:
            TimeoutError: If all retry attempts timeout.
            Exception: If orchestrator fails.
        """
        timeout = settings.api_timeout_seconds
        max_attempts = settings.api_retry_attempts
        retry_delay = settings.api_retry_delay_seconds
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    "orchestrator_attempt",
                    session_id=session_id,
                    attempt=attempt,
                    max_attempts=max_attempts,
                    timeout=timeout
                )
                
                # WAIT FOR GLOBAL SEMAPHORE (Sequential Processing)
                async with self._global_semaphore:
                    logger.info("orchestrator_acquired_semaphore", session_id=session_id)
                    
                    # Run orchestrator with timeout
                    result = await asyncio.wait_for(
                        asyncio.to_thread(
                            self._run_orchestrator_sync,
                            upload_dir,
                            output_dir,
                            progress_callback,
                            bank_statement_months=bank_statement_months,
                            financial_threshold=financial_threshold
                        ),
                        timeout=timeout
                    )
                
                logger.info(
                    "orchestrator_success",
                    session_id=session_id,
                    attempt=attempt
                )
                return result
                
            except asyncio.TimeoutError:
                logger.warning(
                    "orchestrator_timeout",
                    session_id=session_id,
                    attempt=attempt,
                    timeout=timeout
                )
                
                if attempt < max_attempts:
                    # Exponential backoff
                    delay = retry_delay * (2 ** (attempt - 1))
                    logger.info(
                        "orchestrator_retry",
                        session_id=session_id,
                        retry_in_seconds=delay
                    )
                    await asyncio.sleep(delay)
                else:
                    # Final attempt failed
                    error_msg = f"Processing timed out after {max_attempts} attempts ({timeout}s each)"
                    logger.error(
                        "orchestrator_timeout_final",
                        session_id=session_id,
                        total_attempts=max_attempts
                    )
                    raise TimeoutError(error_msg)
                    
            except Exception as e:
                logger.error(
                    "orchestrator_error",
                    session_id=session_id,
                    attempt=attempt,
                    error=str(e)
                )
                # Don't retry on non-timeout errors
                raise

    def _run_orchestrator_sync(
        self,
        upload_dir: Path,
        output_dir: Path,
        progress_callback: ProgressCallback,
        bank_statement_months: int | None = None,
        financial_threshold: float | None = None,
    ):
        """Run the orchestrator synchronously (called from thread pool).

        Args:
            upload_dir: Path to uploaded documents.
            output_dir: Path for output files.
            progress_callback: Callback for progress updates.

        Raises:
            ImportError: If the master orchestrator module cannot be imported.
            Exception: If the orchestrator fails during processing.
        """
        try:
            from master_orchestrator.pipeline.orchestrator import MasterOrchestrator
            from master_orchestrator.config.constants import OutputFormat

            orchestrator = MasterOrchestrator(progress_callback=progress_callback)
            result = orchestrator.process(
                input_folder=upload_dir,
                output_dir=output_dir,
                output_format=OutputFormat.BOTH,
                bank_statement_months=bank_statement_months,
                financial_threshold=financial_threshold,
            )
            return result
        except ImportError as e:
            # Don't silently fall back to simulation - this is a real error
            logger.error(
                "master_orchestrator_import_failed",
                error=str(e),
                hint="Ensure master_orchestrator_agent is installed or path is correct"
            )
            # Re-raise to properly fail the session instead of silently succeeding
            raise ImportError(
                f"Master orchestrator not available: {e}. "
                "Please ensure the master_orchestrator_agent package is installed."
            ) from e

# Global orchestrator runner instance
orchestrator_runner = OrchestratorRunner()
