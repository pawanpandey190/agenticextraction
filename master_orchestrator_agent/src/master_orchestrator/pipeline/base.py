"""Base classes for Master Orchestrator pipeline."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from master_orchestrator.config.settings import Settings
from master_orchestrator.models.input import DocumentInfo, DocumentBatch
from master_orchestrator.models.unified_result import (
    PassportDetails,
    EducationSummary,
    FinancialSummary,
    CrossValidation,
    MasterAnalysisResult,
    ProcessingMetadata,
)


@dataclass
class MasterPipelineContext:
    """Context passed through all pipeline stages."""

    # Input
    input_folder: Path
    settings: Settings

    # Stage 1: Scanned documents
    scanned_documents: list[DocumentInfo] = field(default_factory=list)

    # Stage 2: Classified documents
    document_batch: DocumentBatch | None = None

    # Stage 3: Sub-agent raw results
    passport_raw_result: Any | None = None
    financial_raw_result: Any | None = None
    education_raw_result: Any | None = None

    # Stage 4: Normalized results
    passport_details: PassportDetails | None = None
    financial_summary: FinancialSummary | None = None
    education_summary: EducationSummary | None = None

    # Stage 5: Cross-validation
    cross_validation: CrossValidation | None = None

    # Stage 6: Final result
    final_result: MasterAnalysisResult | None = None

    # Metadata
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def get_metadata(self) -> ProcessingMetadata:
        """Get processing metadata."""
        documents_by_category = {}
        if self.document_batch:
            documents_by_category = {
                "passport": len(self.document_batch.passport_documents),
                "financial": len(self.document_batch.financial_documents),
                "education": len(self.document_batch.education_documents),
                "unknown": len(self.document_batch.unknown_documents),
            }

        return ProcessingMetadata(
            total_documents_scanned=len(self.scanned_documents),
            documents_by_category=documents_by_category,
            processing_errors=self.errors.copy(),
            processing_warnings=self.warnings.copy(),
            processing_time_seconds=self.processing_time_seconds,
        )


class MasterPipelineStage(ABC):
    """Abstract base class for pipeline stages."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage name for logging."""
        pass

    def set_progress_callback(self, callback: Callable | None) -> None:
        """Set an optional progress callback for internal stage progress."""
        self._progress_callback = callback

    @abstractmethod
    def process(self, context: MasterPipelineContext) -> MasterPipelineContext:
        """Process the context and return updated context."""
        pass
