"""Document input and processing models."""

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from ..config.constants import FileType


class DocumentPage(BaseModel):
    """Represents a single page of a document."""

    page_number: int = Field(..., ge=1, description="Page number (1-indexed)")
    image_data: bytes = Field(..., description="Raw image bytes")
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
    mime_type: str = Field(..., description="MIME type of the image")

    model_config = {"arbitrary_types_allowed": True}


class DocumentInput(BaseModel):
    """Input document for processing."""

    file_path: Path = Field(..., description="Path to the document file")
    file_type: FileType = Field(..., description="Detected file type")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    pages: list[DocumentPage] = Field(default_factory=list, description="Document pages")
    original_filename: str = Field(..., description="Original filename")

    @field_validator("file_path", mode="before")
    @classmethod
    def validate_path(cls, v: str | Path) -> Path:
        """Convert string to Path if needed."""
        if isinstance(v, str):
            return Path(v)
        return v

    @property
    def page_count(self) -> int:
        """Get the number of pages."""
        return len(self.pages)


class ProcessingMetadata(BaseModel):
    """Metadata about the document processing."""

    processing_started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When processing started",
    )
    processing_completed_at: datetime | None = Field(
        default=None,
        description="When processing completed",
    )
    ocr_method_used: str | None = Field(
        default=None,
        description="OCR method that was used",
    )
    pages_processed: int = Field(
        default=0,
        ge=0,
        description="Number of pages processed",
    )
    documents_processed: int = Field(
        default=0,
        ge=0,
        description="Number of documents processed",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of non-fatal errors encountered",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of warnings",
    )
    flags: list[str] = Field(
        default_factory=list,
        description="List of processing flags",
    )

    def mark_completed(self) -> None:
        """Mark processing as completed."""
        self.processing_completed_at = datetime.now(UTC)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def add_flag(self, flag: str) -> None:
        """Add a processing flag."""
        if flag not in self.flags:
            self.flags.append(flag)

    @property
    def processing_duration_seconds(self) -> float | None:
        """Get processing duration in seconds."""
        if self.processing_completed_at is None:
            return None
        delta = self.processing_completed_at - self.processing_started_at
        return delta.total_seconds()
