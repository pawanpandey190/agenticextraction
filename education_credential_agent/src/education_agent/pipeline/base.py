"""Base classes for pipeline stages."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import structlog

from ..config.settings import Settings
from ..models.credential_data import CredentialData
from ..models.document import DocumentInput, ProcessingMetadata
from ..models.evaluation import AnalysisResult
from ..models.grade_conversion import GradeConversionTable

logger = structlog.get_logger(__name__)


@dataclass
class PipelineContext:
    """Context passed through pipeline stages for multi-document processing."""

    # Input
    folder_path: str | None = None
    file_paths: list[str] = field(default_factory=list)
    settings: Settings | None = None

    # Grade conversion table
    grade_conversion_table: GradeConversionTable | None = None

    # Processing state - documents
    documents: list[DocumentInput] = field(default_factory=list)

    # Extracted text per document: file_path -> extracted_text
    extracted_texts: dict[str, str] = field(default_factory=dict)

    # First page images for classification: file_path -> (base64, mime_type)
    first_page_images: dict[str, tuple[str, str]] = field(default_factory=dict)

    # Extracted credentials per document
    credentials: list[CredentialData] = field(default_factory=list)

    # Final analysis result
    analysis_result: AnalysisResult | None = None

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

    def add_extracted_text(self, file_path: str, text: str) -> None:
        """Add extracted text for a document.

        Args:
            file_path: Path to the document
            text: Extracted text
        """
        self.extracted_texts[file_path] = text

    def get_extracted_text(self, file_path: str) -> str | None:
        """Get extracted text for a document.

        Args:
            file_path: Path to the document

        Returns:
            Extracted text or None
        """
        return self.extracted_texts.get(file_path)

    def add_first_page_image(self, file_path: str, base64_data: str, mime_type: str) -> None:
        """Add first page image for a document.

        Args:
            file_path: Path to the document
            base64_data: Base64 encoded image
            mime_type: MIME type of the image
        """
        self.first_page_images[file_path] = (base64_data, mime_type)

    def get_first_page_image(self, file_path: str) -> tuple[str, str] | None:
        """Get first page image for a document.

        Args:
            file_path: Path to the document

        Returns:
            Tuple of (base64_data, mime_type) or None
        """
        return self.first_page_images.get(file_path)

    def add_credential(self, credential: CredentialData) -> None:
        """Add an extracted credential.

        Args:
            credential: Extracted credential data
        """
        self.credentials.append(credential)

    def get_credential_by_file(self, file_path: str) -> CredentialData | None:
        """Get credential by source file path.

        Args:
            file_path: Source file path

        Returns:
            CredentialData or None
        """
        for credential in self.credentials:
            if credential.source_file == file_path:
                return credential
        return None


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
            folder_path=context.folder_path,
            file_count=len(context.file_paths),
        )

    def _log_complete(self, context: PipelineContext) -> None:
        """Log stage completion."""
        self.logger.info(
            "Stage completed",
            stage=self.name,
            folder_path=context.folder_path,
        )

    def _log_error(self, error: Exception, context: PipelineContext) -> None:
        """Log stage error."""
        self.logger.error(
            "Stage failed",
            stage=self.name,
            folder_path=context.folder_path,
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
            return result

        except Exception as e:
            self._log_error(e, context)
            context.metadata.add_error(f"{self.name}: {e}")
            raise
