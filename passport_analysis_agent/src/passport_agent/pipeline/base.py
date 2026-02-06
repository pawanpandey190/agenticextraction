"""Base classes for pipeline stages."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import structlog

from ..config.settings import Settings
from ..models.document import PassportDocument, ProcessingMetadata
from ..models.mrz import MRZData
from ..models.passport_data import VisualPassportData
from ..models.result import PassportAnalysisResult
from ..models.validation import CrossValidationResult

logger = structlog.get_logger(__name__)


@dataclass
class PipelineContext:
    """Context passed through pipeline stages."""

    # Input
    file_path: str
    settings: Settings

    # Processing state
    document: PassportDocument | None = None
    preprocessed_images: list[tuple[str, str]] = field(
        default_factory=list
    )  # [(base64, mime_type), ...]
    visual_data: VisualPassportData | None = None
    mrz_raw_text: str | None = None
    mrz_data: MRZData | None = None
    cross_validation: CrossValidationResult | None = None
    final_result: PassportAnalysisResult | None = None

    # Metadata
    metadata: ProcessingMetadata = field(default_factory=ProcessingMetadata)

    # Stage results (for debugging)
    stage_results: dict[str, Any] = field(default_factory=dict)

    def set_stage_result(self, stage_name: str, result: Any) -> None:
        """Store a stage result.

        Args:
            stage_name: Name of the stage
            result: Result from the stage
        """
        self.stage_results[stage_name] = result

    def get_stage_result(self, stage_name: str) -> Any | None:
        """Get a stage result.

        Args:
            stage_name: Name of the stage

        Returns:
            Stage result or None
        """
        return self.stage_results.get(stage_name)

    def add_error(self, error: str) -> None:
        """Add an error to metadata."""
        self.metadata.add_error(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning to metadata."""
        self.metadata.add_warning(warning)


class PipelineStage(ABC):
    """Abstract base class for pipeline stages."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the pipeline stage.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.logger = structlog.get_logger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the stage name."""
        pass

    @abstractmethod
    def process(self, context: PipelineContext) -> PipelineContext:
        """Process the context through this stage.

        Args:
            context: Pipeline context

        Returns:
            Updated context

        Raises:
            Exception: If processing fails
        """
        pass

    def _log_start(self, context: PipelineContext) -> None:
        """Log stage start."""
        self.logger.info(
            "Stage started",
            stage=self.name,
            file_path=context.file_path,
        )

    def _log_complete(self, context: PipelineContext) -> None:
        """Log stage completion."""
        self.logger.info(
            "Stage completed",
            stage=self.name,
            file_path=context.file_path,
        )

    def _log_error(self, error: Exception, context: PipelineContext) -> None:
        """Log stage error."""
        self.logger.error(
            "Stage failed",
            stage=self.name,
            file_path=context.file_path,
            error=str(error),
            error_type=type(error).__name__,
        )

    def execute(self, context: PipelineContext) -> PipelineContext:
        """Execute the stage with logging and error handling.

        Args:
            context: Pipeline context

        Returns:
            Updated context

        Raises:
            Exception: If processing fails
        """
        self._log_start(context)

        try:
            result = self.process(context)
            self._log_complete(context)
            context.metadata.add_stage(self.name)
            return result

        except Exception as e:
            self._log_error(e, context)
            context.metadata.add_error(f"{self.name}: {e}")
            raise
