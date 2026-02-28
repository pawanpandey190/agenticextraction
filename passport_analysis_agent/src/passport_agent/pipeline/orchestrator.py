"""Pipeline orchestrator for passport analysis."""

import structlog

from ..config.settings import Settings
from ..models.result import PassportAnalysisResult
from ..services.llm_service import LLMService
from ..services.mrz_service import MRZService
from .base import PipelineContext, PipelineStage
from .stages import (
    CrossValidatorStage,
    DocumentLoaderStage,
    ImagePreprocessorStage,
    MRZDetectorStage,
    MRZParserStage,
    ScorerStage,
    VisualExtractorStage,
)

logger = structlog.get_logger(__name__)


class PassportPipelineOrchestrator:
    """Orchestrates the passport analysis pipeline."""

    def __init__(
        self,
        settings: Settings,
        llm_service: LLMService | None = None,
        mrz_service: MRZService | None = None,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            settings: Application settings
            llm_service: Optional LLM service instance
            mrz_service: Optional MRZ service instance
        """
        self.settings = settings
        self.llm_service = llm_service or LLMService(settings)
        self.mrz_service = mrz_service or MRZService()

        # Initialize stages in order
        self.stages: list[PipelineStage] = [
            DocumentLoaderStage(settings),
            ImagePreprocessorStage(settings),
            VisualExtractorStage(settings, self.llm_service),
            MRZDetectorStage(settings, self.llm_service),
            MRZParserStage(settings, self.mrz_service),
            CrossValidatorStage(settings),
            ScorerStage(settings),
        ]

    def process(self, file_path: str) -> PassportAnalysisResult:
        """Process a passport document through the pipeline with automatic retry for low scores.

        Args:
            file_path: Path to the passport document

        Returns:
            PassportAnalysisResult with extracted data and scoring

        Raises:
            Exception: If a critical stage fails
        """
        # Run initial attempt
        result = self._run_pipeline(file_path, enhancement_level=0)
        
        # Trigger retry if score is low
        FALLBACK_SCORE_THRESHOLD = 70
        if result.accuracy_score < FALLBACK_SCORE_THRESHOLD:
            logger.info("Low accuracy score detected, retrying with high enhancement", 
                        score=result.accuracy_score, threshold=FALLBACK_SCORE_THRESHOLD)
            
            retry_result = self._run_pipeline(file_path, enhancement_level=1)
            
            if retry_result.accuracy_score > result.accuracy_score:
                logger.info("Retry improved the score", 
                            old_score=result.accuracy_score, 
                            new_score=retry_result.accuracy_score)
                result = retry_result
            else:
                logger.info("Retry did not improve the score, keeping original")

        return result

    def _run_pipeline(self, file_path: str, enhancement_level: int = 0) -> PassportAnalysisResult:
        """Run the pipeline stages for a specific enhancement level."""
        logger.info("Running pipeline", file_path=file_path, enhancement_level=enhancement_level)

        # Create context
        context = PipelineContext(
            file_path=file_path,
            settings=self.settings,
            enhancement_level=enhancement_level
        )

        # Run each stage
        for stage in self.stages:
            try:
                context = stage.execute(context)
            except Exception as e:
                logger.error(
                    "Pipeline stage failed",
                    stage=stage.name,
                    error=str(e),
                )
                # For critical early stages, re-raise
                if stage.name in ("DocumentLoader", "VisualExtractor"):
                    raise

                # For other stages, continue with degraded results
                context.add_error(f"Stage {stage.name} failed: {e}")

        # Ensure we have a result
        if context.final_result is None:
            # Create minimal result if scorer didn't run
            from ..models.passport_data import VisualPassportData

            context.final_result = PassportAnalysisResult(
                extracted_passport_data=context.visual_data or VisualPassportData(),
                extracted_mrz_data=context.mrz_data,
                processing_errors=context.metadata.errors,
                processing_warnings=context.metadata.warnings,
                source_file=file_path,
                accuracy_score=0,
                confidence_level="LOW",
                remarks=f"Analysis failed to complete full scoring. Errors: {', '.join(context.metadata.errors)}" if context.metadata.errors else "Analysis incomplete due to pipeline interruption."
            )

        context.final_result.processing_time_seconds = context.metadata.processing_time_seconds
        return context.final_result

    def process_batch(self, file_paths: list[str]) -> list[PassportAnalysisResult]:
        """Process multiple passport documents.

        Args:
            file_paths: List of file paths to process

        Returns:
            List of PassportAnalysisResult
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.process(file_path)
                results.append(result)
            except Exception as e:
                logger.error("Failed to process file", file_path=file_path, error=str(e))
                # Create error result
                from ..models.passport_data import VisualPassportData

                error_result = PassportAnalysisResult(
                    extracted_passport_data=VisualPassportData(),
                    processing_errors=[str(e)],
                    source_file=file_path,
                )
                results.append(error_result)

        return results
