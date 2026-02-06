"""Batch upload management service."""

import uuid
from datetime import datetime
from typing import Dict

import structlog

from app.models.api_models import BatchSessionInfo, BatchStatusResponse
from app.models.session import Session, SessionStatus

logger = structlog.get_logger(__name__)


class BatchUpload:
    """Represents a batch upload of student folders."""

    def __init__(self, batch_id: str, student_sessions: list[str]):
        """Initialize a batch upload.

        Args:
            batch_id: Unique identifier for the batch.
            student_sessions: List of session IDs in this batch.
        """
        self.batch_id = batch_id
        self._student_sessions = student_sessions
        self.created_at = datetime.utcnow()
        self.total_students = len(student_sessions)

    @property
    def student_sessions(self) -> list[str]:
        return self._student_sessions

    @student_sessions.setter
    def student_sessions(self, value: list[str]):
        self._student_sessions = value
        self.total_students = len(value)

    def get_status(self, sessions: list[Session]) -> str:
        """Calculate batch status based on session statuses.

        Args:
            sessions: List of sessions in this batch.

        Returns:
            Batch status string.
        """
        if not sessions:
            return "created"

        statuses = [s.status for s in sessions]
        
        # All completed
        if all(s == SessionStatus.COMPLETED for s in statuses):
            return "completed"
        
        # All failed
        if all(s == SessionStatus.FAILED for s in statuses):
            return "failed"
        
        # Any processing
        if any(s == SessionStatus.PROCESSING for s in statuses):
            return "processing"
        
        # Mix of completed and failed
        if any(s == SessionStatus.COMPLETED for s in statuses) and any(s == SessionStatus.FAILED for s in statuses):
            return "partial_failure"
        
        return "created"

    def count_by_status(self, sessions: list[Session]) -> dict[str, int]:
        """Count sessions by status.

        Args:
            sessions: List of sessions in this batch.

        Returns:
            Dictionary with counts for each status.
        """
        counts = {
            "created": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        }
        
        for session in sessions:
            if session.status == SessionStatus.CREATED or session.status == SessionStatus.UPLOADING:
                counts["created"] += 1
            elif session.status == SessionStatus.PROCESSING:
                counts["processing"] += 1
            elif session.status == SessionStatus.COMPLETED:
                counts["completed"] += 1
            elif session.status == SessionStatus.FAILED:
                counts["failed"] += 1
        
        return counts


class BatchManager:
    """Manages batch uploads and their sessions."""

    def __init__(self):
        """Initialize the batch manager."""
        self._batches: Dict[str, BatchUpload] = {}
        logger.info("batch_manager_initialized")

    def create_batch(self, student_sessions: list[str]) -> BatchUpload:
        """Create a new batch upload.

        Args:
            student_sessions: List of session IDs for students in this batch.

        Returns:
            Created BatchUpload instance.
        """
        batch_id = str(uuid.uuid4())
        batch = BatchUpload(batch_id, student_sessions)
        self._batches[batch_id] = batch
        
        logger.info(
            "batch_created",
            batch_id=batch_id,
            total_students=len(student_sessions),
        )
        
        return batch

    def reconstruct_batch(self, batch_id: str, student_sessions: list[str]) -> BatchUpload:
        """Reconstruct a batch from existing sessions (e.g. after reload)."""
        batch = BatchUpload(batch_id, student_sessions)
        self._batches[batch_id] = batch
        logger.info("batch_reconstructed", batch_id=batch_id, students=len(student_sessions))
        return batch

    def get_batch(self, batch_id: str) -> BatchUpload | None:
        """Get a batch by ID.

        Args:
            batch_id: Batch identifier.

        Returns:
            BatchUpload instance or None if not found.
        """
        return self._batches.get(batch_id)

    def list_batches(self) -> list[BatchUpload]:
        """List all batches.

        Returns:
            List of all BatchUpload instances.
        """
        return list(self._batches.values())

    def get_batch_status(
        self,
        batch_id: str,
        sessions: list[Session],
    ) -> BatchStatusResponse | None:
        """Get detailed status of a batch.

        Args:
            batch_id: Batch identifier.
            sessions: List of sessions in the batch.

        Returns:
            BatchStatusResponse or None if batch not found.
        """
        batch = self.get_batch(batch_id)
        if not batch:
            return None

        status = batch.get_status(sessions)
        counts = batch.count_by_status(sessions)

        session_infos = [
            BatchSessionInfo(
                session_id=s.id,
                student_name=s.student_name or "Unknown",
                status=s.status,
                total_files=s.total_files,
                result_available=s.result_available,
                letter_available=s.letter_available,
                current_document=s.current_document,
                processed_documents=s.processed_documents,
                total_documents=s.total_documents,
                progress_percentage=s.progress_percentage,
            )
            for s in sessions
        ]

        return BatchStatusResponse(
            batch_id=batch_id,
            status=status,
            total_students=batch.total_students,
            completed=counts["completed"],
            processing=counts["processing"],
            failed=counts["failed"],
            created=counts["created"],
            sessions=session_infos,
        )

    def delete_batch(self, batch_id: str) -> bool:
        """Delete a batch.

        Args:
            batch_id: Batch identifier.

        Returns:
            True if deleted, False if not found.
        """
        if batch_id in self._batches:
            del self._batches[batch_id]
            logger.info("batch_deleted", batch_id=batch_id)
            return True
        return False


# Global batch manager instance
batch_manager = BatchManager()
