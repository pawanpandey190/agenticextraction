"""Progress event models."""

from pydantic import BaseModel, Field


class ProgressUpdate(BaseModel):
    """Progress update from the orchestrator."""

    stage_name: str
    stage_index: int
    total_stages: int
    sub_agent: str | None = None
    sub_stage_name: str | None = None
    sub_stage_index: int | None = None
    sub_total_stages: int | None = None
    message: str = ""
    
    # Document-level tracking
    current_document: str | None = None
    processed_documents: int = 0
    total_documents: int = 0


class ProgressEvent(BaseModel):
    """Progress event sent to the frontend via SSE."""

    stage_name: str = Field(description="Current stage name")
    stage_index: int = Field(description="0-based stage index")
    total_stages: int = Field(default=6, description="Total number of stages")
    message: str = Field(description="Human-readable status message")
    percentage: float = Field(description="Progress percentage (0-100)")
    sub_agent: str | None = Field(default=None, description="Sub-agent being processed")
    completed: bool = Field(default=False, description="Whether processing is complete")
    error: str | None = Field(default=None, description="Error message if failed")
    
    # Document-level tracking
    current_document: str | None = Field(default=None, description="Current document being processed")
    processed_documents: int = Field(default=0, description="Number of documents processed")
    total_documents: int = Field(default=0, description="Total documents to process")

    @classmethod
    def from_update(cls, update: ProgressUpdate) -> "ProgressEvent":
        """Create a ProgressEvent from a ProgressUpdate."""
        percentage = ((update.stage_index + 1) / update.total_stages) * 100
        
        # Build message with document info if available
        message = update.message or f"Processing {update.stage_name}..."
        if update.current_document:
            message = f"Processing {update.current_document} ({update.processed_documents + 1}/{update.total_documents})"
        
        return cls(
            stage_name=update.stage_name,
            stage_index=update.stage_index,
            total_stages=update.total_stages,
            message=message,
            percentage=percentage,
            sub_agent=update.sub_agent,
            current_document=update.current_document,
            processed_documents=update.processed_documents,
            total_documents=update.total_documents,
        )

    @classmethod
    def completed_event(cls) -> "ProgressEvent":
        """Create a completion event."""
        return cls(
            stage_name="Complete",
            stage_index=6,
            total_stages=6,
            message="Processing complete",
            percentage=100.0,
            completed=True,
        )

    @classmethod
    def error_event(cls, error_message: str, stage_name: str = "Error") -> "ProgressEvent":
        """Create an error event."""
        return cls(
            stage_name=stage_name,
            stage_index=0,
            total_stages=6,
            message=error_message,
            percentage=0.0,
            error=error_message,
        )
