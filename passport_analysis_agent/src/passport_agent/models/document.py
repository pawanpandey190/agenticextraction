"""Document models for passport processing."""

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, computed_field

from ..config.constants import FileType


class PassportPage(BaseModel):
    """Represents a single page/image from a passport document."""

    page_number: int = Field(ge=1, description="Page number (1-indexed)")
    image_base64: str = Field(description="Base64 encoded image data")
    mime_type: str = Field(description="MIME type of the image")
    width: int = Field(ge=1, description="Image width in pixels")
    height: int = Field(ge=1, description="Image height in pixels")

    model_config = {"extra": "forbid"}


class PassportDocument(BaseModel):
    """Represents a passport document input."""

    file_path: str = Field(description="Path to the source file")
    file_type: FileType = Field(description="Detected file type")
    file_size_bytes: int = Field(ge=0, description="File size in bytes")
    pages: list[PassportPage] = Field(
        default_factory=list, description="Extracted pages"
    )
    loaded_at: datetime = Field(
        default_factory=datetime.utcnow, description="When document was loaded"
    )

    model_config = {"extra": "forbid"}

    @computed_field
    @property
    def page_count(self) -> int:
        """Get the number of pages."""
        return len(self.pages)

    @computed_field
    @property
    def file_name(self) -> str:
        """Get the file name from the path."""
        return Path(self.file_path).name

    @computed_field
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return round(self.file_size_bytes / (1024 * 1024), 2)


class ProcessingMetadata(BaseModel):
    """Metadata about the processing pipeline."""

    started_at: datetime = Field(
        default_factory=datetime.utcnow, description="Processing start time"
    )
    completed_at: datetime | None = Field(
        default=None, description="Processing completion time"
    )
    stages_completed: list[str] = Field(
        default_factory=list, description="List of completed stage names"
    )
    errors: list[str] = Field(
        default_factory=list, description="List of error messages"
    )
    warnings: list[str] = Field(
        default_factory=list, description="List of warning messages"
    )

    model_config = {"extra": "forbid"}

    def add_stage(self, stage_name: str) -> None:
        """Mark a stage as completed."""
        if stage_name not in self.stages_completed:
            self.stages_completed.append(stage_name)

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def mark_completed(self) -> None:
        """Mark processing as completed."""
        self.completed_at = datetime.utcnow()

    @computed_field
    @property
    def processing_time_seconds(self) -> float | None:
        """Get processing time in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()
