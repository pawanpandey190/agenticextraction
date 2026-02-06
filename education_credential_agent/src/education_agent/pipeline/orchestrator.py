"""Pipeline orchestrator for document processing."""

import structlog

from ..config.settings import Settings
from ..models.evaluation import AnalysisResult
from ..services.grade_table_service import GradeTableService
from ..services.llm_service import LLMService
from ..utils.exceptions import EducationAgentError
from .base import PipelineContext, PipelineStage
from .stages.classifier import ClassifierStage
from .stages.document_loader import DocumentLoaderStage
from .stages.evaluator import EvaluatorStage
from .stages.extractor import ExtractorStage
from .stages.grade_converter import GradeConverterStage
from .stages.ocr_processor import OCRProcessorStage
from .stages.semester_validator import SemesterValidatorStage

logger = structlog.get_logger(__name__)


class PipelineOrchestrator:
    """Orchestrates the document processing pipeline for multiple documents."""

    def __init__(
        self,
        settings: Settings,
        grade_table_path: str | None = None,
    ) -> None:
        """Initialize the pipeline orchestrator.

        Args:
            settings: Application settings
            grade_table_path: Path to grade conversion table file
        """
        self.settings = settings

        # Initialize shared services
        self.llm_service = LLMService(settings)
        self.grade_table_service = GradeTableService(grade_table_path)

        # Load grade table if path provided
        if grade_table_path:
            self.grade_table_service.load_table()

        # Initialize stages
        self.stages: list[PipelineStage] = [
            DocumentLoaderStage(settings),
            OCRProcessorStage(settings, self.llm_service),
            ClassifierStage(settings, self.llm_service),
            ExtractorStage(settings, self.llm_service),
            SemesterValidatorStage(settings),
            GradeConverterStage(settings, self.grade_table_service),
            EvaluatorStage(settings),
        ]

        logger.info(
            "Pipeline orchestrator initialized",
            stage_count=len(self.stages),
            grade_table_path=grade_table_path,
        )

    def process_folder(self, folder_path: str) -> AnalysisResult:
        """Process all documents in a folder.

        Args:
            folder_path: Path to folder containing documents

        Returns:
            Analysis result

        Raises:
            EducationAgentError: If processing fails
        """
        logger.info("Starting folder processing", folder_path=folder_path)

        # Create pipeline context
        context = PipelineContext(
            folder_path=folder_path,
            settings=self.settings,
            grade_conversion_table=self.grade_table_service.get_table(),
        )

        return self._execute_pipeline(context)

    def process_files(self, file_paths: list[str]) -> AnalysisResult:
        """Process specific files.

        Args:
            file_paths: List of file paths to process

        Returns:
            Analysis result

        Raises:
            EducationAgentError: If processing fails
        """
        logger.info("Starting file processing", file_count=len(file_paths))

        # Create pipeline context
        context = PipelineContext(
            file_paths=file_paths,
            settings=self.settings,
            grade_conversion_table=self.grade_table_service.get_table(),
        )

        return self._execute_pipeline(context)

    def process(
        self,
        folder_path: str | None = None,
        file_paths: list[str] | None = None,
    ) -> AnalysisResult:
        """Process documents from folder and/or file list.

        Args:
            folder_path: Optional folder path
            file_paths: Optional list of file paths

        Returns:
            Analysis result

        Raises:
            EducationAgentError: If processing fails
        """
        if not folder_path and not file_paths:
            raise EducationAgentError("Either folder_path or file_paths must be provided")

        logger.info(
            "Starting document processing",
            folder_path=folder_path,
            file_count=len(file_paths) if file_paths else 0,
        )

        # Create pipeline context
        context = PipelineContext(
            folder_path=folder_path,
            file_paths=file_paths or [],
            settings=self.settings,
            grade_conversion_table=self.grade_table_service.get_table(),
        )

        return self._execute_pipeline(context)

    def _execute_pipeline(self, context: PipelineContext) -> AnalysisResult:
        """Execute the pipeline stages.

        Args:
            context: Pipeline context

        Returns:
            Analysis result

        Raises:
            EducationAgentError: If pipeline fails
        """
        try:
            # Execute each stage
            for stage in self.stages:
                context = stage.execute(context)

            # Mark processing complete
            context.metadata.mark_completed()

            logger.info(
                "Pipeline processing completed",
                folder_path=context.folder_path,
                duration_seconds=context.metadata.processing_duration_seconds,
                documents_processed=context.metadata.documents_processed,
                errors=len(context.metadata.errors),
                warnings=len(context.metadata.warnings),
            )

            if context.analysis_result is None:
                raise EducationAgentError("Pipeline completed but no analysis result generated")

            return context.analysis_result

        except Exception as e:
            logger.error(
                "Pipeline processing failed",
                folder_path=context.folder_path,
                error=str(e),
                error_type=type(e).__name__,
            )

            context.metadata.mark_completed()

            if isinstance(e, EducationAgentError):
                raise

            raise EducationAgentError(f"Pipeline failed: {e}") from e

    def process_with_context(
        self,
        folder_path: str | None = None,
        file_paths: list[str] | None = None,
    ) -> tuple[AnalysisResult, PipelineContext]:
        """Process documents and return both result and context.

        Args:
            folder_path: Optional folder path
            file_paths: Optional list of file paths

        Returns:
            Tuple of (AnalysisResult, PipelineContext)

        Raises:
            EducationAgentError: If processing fails
        """
        if not folder_path and not file_paths:
            raise EducationAgentError("Either folder_path or file_paths must be provided")

        logger.info(
            "Starting document processing with context",
            folder_path=folder_path,
            file_count=len(file_paths) if file_paths else 0,
        )

        # Create pipeline context
        context = PipelineContext(
            folder_path=folder_path,
            file_paths=file_paths or [],
            settings=self.settings,
            grade_conversion_table=self.grade_table_service.get_table(),
        )

        try:
            # Execute each stage
            for stage in self.stages:
                context = stage.execute(context)

            # Mark processing complete
            context.metadata.mark_completed()

            logger.info(
                "Pipeline processing completed",
                folder_path=context.folder_path,
                duration_seconds=context.metadata.processing_duration_seconds,
            )

            if context.analysis_result is None:
                raise EducationAgentError("Pipeline completed but no analysis result generated")

            return context.analysis_result, context

        except Exception as e:
            logger.error(
                "Pipeline processing failed",
                folder_path=context.folder_path,
                error=str(e),
            )

            context.metadata.mark_completed()

            if isinstance(e, EducationAgentError):
                raise

            raise EducationAgentError(f"Pipeline failed: {e}") from e
