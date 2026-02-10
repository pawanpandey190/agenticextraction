"""Pipeline orchestrator for document processing."""

import structlog

from ..config.settings import Settings
from ..models.financial_data import AnalysisResult
from ..services.exchange_service import ExchangeService
from ..services.llm_service import LLMService
from ..utils.exceptions import FinancialAgentError
from .base import PipelineContext, PipelineStage
from .stages.classifier import ClassifierStage
from .stages.currency_converter import CurrencyConverterStage
from .stages.document_loader import DocumentLoaderStage
from .stages.evaluator import EvaluatorStage
from .stages.extractor import ExtractorStage
from .stages.ocr_processor import OCRProcessorStage

logger = structlog.get_logger(__name__)


class PipelineOrchestrator:
    """Orchestrates the document processing pipeline."""

    def __init__(
        self,
        settings: Settings,
        threshold_eur: float | None = None,
        required_period_months: int | None = None,
    ) -> None:
        """Initialize the pipeline orchestrator.

        Args:
            settings: Application settings
            threshold_eur: Optional override for worthiness threshold
            required_period_months: Optional required bank statement period in months
        """
        self.settings = settings
        self.threshold_eur = threshold_eur or settings.worthiness_threshold_eur
        self.required_period_months = required_period_months

        # Initialize shared services
        self.llm_service = LLMService(settings)
        self.exchange_service = ExchangeService(settings)

        # Initialize stages
        self.stages: list[PipelineStage] = [
            DocumentLoaderStage(settings),
            OCRProcessorStage(settings, self.llm_service),
            ClassifierStage(settings, self.llm_service),
            ExtractorStage(settings, self.llm_service),
            CurrencyConverterStage(settings, self.exchange_service),
            EvaluatorStage(settings, self.threshold_eur, self.required_period_months),
        ]

        logger.info(
            "Pipeline orchestrator initialized",
            stage_count=len(self.stages),
            threshold_eur=self.threshold_eur,
        )

    def process(self, file_path: str) -> AnalysisResult:
        """Process a document through the pipeline.

        Args:
            file_path: Path to the document file

        Returns:
            Analysis result

        Raises:
            FinancialAgentError: If processing fails
        """
        logger.info("Starting document processing", file_path=file_path)

        # Create pipeline context
        context = PipelineContext(
            file_path=file_path,
            settings=self.settings,
        )

        try:
            # Execute each stage
            for stage in self.stages:
                context = stage.execute(context)

            # Mark processing complete
            context.metadata.mark_completed()

            logger.info(
                "Document processing completed",
                file_path=file_path,
                duration_seconds=context.metadata.processing_duration_seconds,
                errors=len(context.metadata.errors),
                warnings=len(context.metadata.warnings),
            )

            if context.analysis_result is None:
                raise FinancialAgentError("Pipeline completed but no analysis result generated")

            return context.analysis_result

        except Exception as e:
            logger.error(
                "Document processing failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
            )

            context.metadata.mark_completed()

            if isinstance(e, FinancialAgentError):
                raise

            raise FinancialAgentError(f"Pipeline failed: {e}") from e

        finally:
            # Cleanup
            self.exchange_service.close()

    def process_with_context(self, file_path: str) -> tuple[AnalysisResult, PipelineContext]:
        """Process a document and return both result and context.

        Args:
            file_path: Path to the document file

        Returns:
            Tuple of (AnalysisResult, PipelineContext)

        Raises:
            FinancialAgentError: If processing fails
        """
        logger.info("Starting document processing with context", file_path=file_path)

        # Create pipeline context
        context = PipelineContext(
            file_path=file_path,
            settings=self.settings,
        )

        try:
            # Execute each stage
            for stage in self.stages:
                context = stage.execute(context)

            # Mark processing complete
            context.metadata.mark_completed()

            logger.info(
                "Document processing completed",
                file_path=file_path,
                duration_seconds=context.metadata.processing_duration_seconds,
            )

            if context.analysis_result is None:
                raise FinancialAgentError("Pipeline completed but no analysis result generated")

            return context.analysis_result, context

        except Exception as e:
            logger.error(
                "Document processing failed",
                file_path=file_path,
                error=str(e),
            )

            context.metadata.mark_completed()

            if isinstance(e, FinancialAgentError):
                raise

            raise FinancialAgentError(f"Pipeline failed: {e}") from e

        finally:
            # Cleanup
            self.exchange_service.close()
