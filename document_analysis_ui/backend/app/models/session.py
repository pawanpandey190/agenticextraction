"""Session state models."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
import uuid


class SessionStatus(str, Enum):
    """Status of a processing session."""

    CREATED = "created"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Session(BaseModel):
    """Represents a document processing session."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: SessionStatus = SessionStatus.CREATED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Document info
    uploaded_files: list[str] = Field(default_factory=list)
    total_files: int = 0

    # Processing config
    financial_threshold: float = 15000.0

    # Batch upload support (optional fields for backward compatibility)
    batch_id: str | None = None  # Links to batch if part of batch upload
    student_name: str | None = None  # Student identifier from folder name
    student_folder: str | None = None  # Original folder name for reference

    # Progress tracking
    current_document: str | None = None  # Current document being processed
    processed_documents: int = 0  # Number of documents processed so far
    total_documents: int = 0  # Total number of documents to process
    progress_percentage: float = 0.0  # Progress as percentage (0-100)

    # Results
    result_available: bool = False
    letter_available: bool = False
    error_message: str | None = None

    def get_upload_dir(self, base_path: Path) -> Path:
        """Get the upload directory for this session."""
        return base_path / self.id / "uploads"

    def get_output_dir(self, base_path: Path) -> Path:
        """Get the output directory for this session."""
        return base_path / self.id / "output"

    def update_status(self, status: SessionStatus) -> None:
        """Update the session status."""
        self.status = status
        self.updated_at = datetime.utcnow()
