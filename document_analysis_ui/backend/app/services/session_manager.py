"""Session lifecycle management."""

import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterator

import structlog

from app.config import settings
from app.models.session import Session, SessionStatus

logger = structlog.get_logger(__name__)


class SessionManager:
    """Manages session lifecycle and storage."""

    def __init__(self, base_path: Path | None = None):
        """Initialize the session manager.

        Args:
            base_path: Base path for session storage. Defaults to settings.
        """
        self._base_path = base_path or settings.session_base_path
        self._sessions: dict[str, Session] = {}
        self._batch_sessions: dict[str, set[str]] = {}  # batch_id -> set of session_ids
        self._last_mtimes: dict[str, float] = {}  # session_id -> last known mtime
        
        self._ensure_base_dir()
        self._warm_cache()

    def _ensure_base_dir(self) -> None:
        """Ensure the base directory exists."""
        self._base_path.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_id: str) -> Path:
        """Get the path to the session metadata file."""
        return self._base_path / session_id / "session.json"

    def _save_session(self, session: Session) -> None:
        """Save session to disk."""
        session_dir = self._base_path / session.id
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = self._get_session_file(session.id)
        session_file.write_text(session.model_dump_json(indent=2))
        
        # Update batch mapping and mtime
        session_file = self._get_session_file(session.id)
        if session_file.exists():
            self._last_mtimes[session.id] = session_file.stat().st_mtime

        if session.batch_id:
            if session.batch_id not in self._batch_sessions:
                self._batch_sessions[session.batch_id] = set()
            self._batch_sessions[session.batch_id].add(session.id)

    def _load_session(self, session_id: str) -> Session | None:
        """Load session from disk."""
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text())
                session = Session(**data)
                # Update mtime cache
                self._last_mtimes[session_id] = session_file.stat().st_mtime
                # Ensure mapping is updated
                if session.batch_id:
                    if session.batch_id not in self._batch_sessions:
                        self._batch_sessions[session.batch_id] = set()
                    self._batch_sessions[session.batch_id].add(session.id)
                return session
            except Exception:
                logger.error("failed_to_load_session", session_id=session_id)
                return None
        return None

    def _warm_cache(self) -> None:
        """Load all sessions from disk on startup to warm the cache and mappings."""
        logger.info("warming_session_cache")
        if not self._base_path.exists():
            return
            
        for session_dir in self._base_path.iterdir():
            if session_dir.is_dir():
                try:
                    session = self._load_session(session_dir.name)
                    if session:
                        self._sessions[session.id] = session
                except Exception:
                    continue
        logger.info("cache_warmed", session_count=len(self._sessions))

    def create_session(
        self,
        financial_threshold: float = 15000.0,
        bank_statement_period: int = 3,
        batch_id: str | None = None,
        student_name: str | None = None,
        student_folder: str | None = None,
    ) -> Session:
        """Create a new session.

        Args:
            financial_threshold: Financial worthiness threshold in EUR.
            bank_statement_period: Required bank statement period in months.
            batch_id: Optional batch ID if part of batch upload.
            student_name: Optional student name from folder.
            student_folder: Optional original folder name.

        Returns:
            New Session instance.
        """
        session = Session(
            financial_threshold=financial_threshold,
            bank_statement_period=bank_statement_period,
            batch_id=batch_id,
            student_name=student_name,
            student_folder=student_folder,
        )

        # Create session directories
        upload_dir = session.get_upload_dir(self._base_path)
        output_dir = session.get_output_dir(self._base_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save session
        self._save_session(session)
        self._sessions[session.id] = session

        logger.info(
            "session_created",
            session_id=session.id,
            batch_id=batch_id,
            student_name=student_name,
        )
        return session

    def create_batch_sessions(
        self,
        student_folders: dict[str, list[str]],
        batch_id: str,
        financial_threshold: float = 15000.0,
        bank_statement_period: int = 3,
    ) -> list[Session]:
        """Create multiple sessions for batch upload.

        Args:
            student_folders: Dictionary mapping student names to their file lists.
            batch_id: Batch identifier to link sessions.
            financial_threshold: Financial threshold for all sessions.
            bank_statement_period: Bank statement period for all sessions.

        Returns:
            List of created Session instances.
        """
        sessions = []
        for student_name, files in student_folders.items():
            session = self.create_session(
                financial_threshold=financial_threshold,
                bank_statement_period=bank_statement_period,
                batch_id=batch_id,
                student_name=student_name,
                student_folder=student_name,
            )
            sessions.append(session)
            logger.info(
                "batch_session_created",
                session_id=session.id,
                batch_id=batch_id,
                student_name=student_name,
                file_count=len(files),
            )
        return sessions

    def get_sessions_by_batch(self, batch_id: str) -> list[Session]:
        """Get all sessions belonging to a batch.

        Args:
            batch_id: Batch identifier.

        Returns:
            List of sessions in the batch.
        """
        session_ids = self._batch_sessions.get(batch_id, set())
        sessions = []
        for sid in session_ids:
            session = self.get_session(sid)
            if session:
                sessions.append(session)
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID, reloading if updated on disk."""
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            self._sessions.pop(session_id, None)
            return None

        current_mtime = session_file.stat().st_mtime
        cached_mtime = self._last_mtimes.get(session_id, 0)

        # Reload if not in cache OR if file has been modified
        if session_id not in self._sessions or current_mtime > cached_mtime:
            session = self._load_session(session_id)
            if session:
                self._sessions[session_id] = session
                return session
            return None

        return self._sessions.get(session_id)

    def update_session(self, session: Session) -> None:
        """Update a session.

        Args:
            session: Session to update.
        """
        session.updated_at = datetime.utcnow()
        self._sessions[session.id] = session
        self._save_session(session)
        logger.info("session_updated", session_id=session.id, status=session.status)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its files, revoking any active task."""
        session = self.get_session(session_id)
        if not session:
            # Check if directory exists even if not in cache
            session_dir = self._base_path / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
                return True
            return False

        # 1. Revoke active task if any
        if session.status == SessionStatus.PROCESSING and session.celery_task_id:
            try:
                from app.celery_app import celery_app
                logger.info("revoking_task_before_deletion", session_id=session_id, task_id=session.celery_task_id)
                celery_app.control.revoke(session.celery_task_id, terminate=True, signal='SIGKILL')
            except Exception as e:
                logger.error("failed_to_revoke_task_on_deletion", session_id=session_id, error=str(e))

        # 2. Delete files
        session_dir = self._base_path / session_id
        if session_dir.exists():
            shutil.rmtree(session_dir)
            self._sessions.pop(session_id, None)
            logger.info("session_deleted", session_id=session_id)
            return True
        return False

    def list_sessions(self) -> list[Session]:
        """List all sessions, refreshing from disk."""
        # Force re-scan of directory to find new sessions or external updates
        if self._base_path.exists():
            for session_dir in self._base_path.iterdir():
                if session_dir.is_dir():
                    # This will trigger the mtime check in get_session
                    self.get_session(session_dir.name)
            
        return sorted(self._sessions.values(), key=lambda s: s.created_at, reverse=True)

    def resolve_duplicate_name(self, name: str, current_session_id: str) -> str:
        """Resolve a student name to avoid duplicates in history.
        
        If name exists, appends " 1", " 2", etc.
        """
        if not name:
            return name
            
        sessions = self.list_sessions()
        existing_names = [
            s.student_name for s in sessions 
            if s.id != current_session_id and s.student_name
        ]
        
        if name not in existing_names:
            return name
            
        # Increment until we find a name that's not taken
        counter = 1
        new_name = f"{name} {counter}"
        while new_name in existing_names:
            counter += 1
            new_name = f"{name} {counter}"
            
        logger.info("resolved_duplicate_name", original=name, resolved=new_name, session_id=current_session_id)
        return new_name

    def cleanup_expired_sessions(self, expiry_hours: int | None = None) -> int:
        """Remove sessions older than expiry time.

        Args:
            expiry_hours: Hours after which sessions expire. Defaults to settings.

        Returns:
            Number of sessions cleaned up.
        """
        expiry_hours = expiry_hours or settings.session_expiry_hours
        cutoff = datetime.utcnow() - timedelta(hours=expiry_hours)
        cleaned = 0

        for session in self.list_sessions():
            if session.created_at < cutoff:
                self.delete_session(session.id)
                cleaned += 1

        if cleaned > 0:
            logger.info("sessions_cleaned_up", count=cleaned)
        return cleaned

    def get_upload_dir(self, session_id: str) -> Path | None:
        """Get the upload directory for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Path to upload directory, or None if session not found.
        """
        session = self.get_session(session_id)
        if session:
            return session.get_upload_dir(self._base_path)
        return None

    def get_output_dir(self, session_id: str) -> Path | None:
        """Get the output directory for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Path to output directory, or None if session not found.
        """
        session = self.get_session(session_id)
        if session:
            return session.get_output_dir(self._base_path)
        return None


# Global session manager instance
session_manager = SessionManager()
