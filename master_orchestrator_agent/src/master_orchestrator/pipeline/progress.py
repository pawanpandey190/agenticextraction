"""Progress tracking for the Master Orchestrator pipeline."""

from dataclasses import dataclass
from typing import Callable, Protocol


@dataclass
class ProgressUpdate:
    """Represents a progress update from the orchestrator."""

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


class ProgressCallback(Protocol):
    """Protocol for progress callback functions."""

    def __call__(self, update: ProgressUpdate) -> None:
        """Handle a progress update.

        Args:
            update: The progress update to handle.
        """
        ...


# Type alias for the callback
ProgressCallbackType = Callable[[ProgressUpdate], None] | None
