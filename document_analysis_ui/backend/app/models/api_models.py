"""Request/response models for the API."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from app.models.session import SessionStatus


class CreateSessionRequest(BaseModel):
    """Request to create a new session."""

    financial_threshold: float = Field(default=15000.0, description="Financial worthiness threshold in EUR")


class CreateSessionResponse(BaseModel):
    """Response after creating a session."""

    session_id: str
    status: SessionStatus
    upload_url: str


class SessionResponse(BaseModel):
    """Session information response."""

    id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    uploaded_files: list[str]
    total_files: int
    financial_threshold: float
    result_available: bool
    letter_available: bool = False
    error_message: str | None = None
    # Batch support
    batch_id: str | None = None
    student_name: str | None = None
    # Progress tracking
    current_document: str | None = None
    processed_documents: int = 0
    total_documents: int = 0
    progress_percentage: float = 0.0


class UploadResponse(BaseModel):
    """Response after uploading files."""

    uploaded_files: list[str]
    total_files: int


class ProcessRequest(BaseModel):
    """Request to start processing."""

    # Additional processing options can be added here
    pass


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str
    error_code: str | None = None


# Batch Upload Models

class BatchStatus(str, Enum):
    """Status of a batch upload."""
    
    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


class BatchSessionInfo(BaseModel):
    """Information about a session in a batch."""
    
    session_id: str
    student_name: str
    status: SessionStatus
    total_files: int = 0
    result_available: bool = False
    letter_available: bool = False
    # Progress tracking
    current_document: str | None = None
    processed_documents: int = 0
    total_documents: int = 0
    progress_percentage: float = 0.0


class BatchUploadResponse(BaseModel):
    """Response after uploading a batch of student folders."""
    
    batch_id: str
    total_students: int
    sessions: list[BatchSessionInfo]
    message: str = "Batch upload successful"


class BatchStatusResponse(BaseModel):
    """Status response for a batch."""
    
    batch_id: str
    status: str  # BatchStatus values
    total_students: int
    completed: int = 0
    processing: int = 0
    failed: int = 0
    created: int = 0
    sessions: list[BatchSessionInfo]


class DocumentMetadata(BaseModel):
    """Metadata about an uploaded document."""
    
    filename: str
    size: int
    type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)

class ManualLetterRequest(BaseModel):
    """Request to generate a letter with manual data."""

    student_name: str | None = None
    date: str | None = None  # Flexible date format
