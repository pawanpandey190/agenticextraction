"""Master Orchestrator - Main entry point for document processing."""

import time
from pathlib import Path

import structlog

from master_orchestrator.config.settings import Settings
from master_orchestrator.config.constants import OutputFormat
from master_orchestrator.models.unified_result import MasterAnalysisResult
from master_orchestrator.pipeline.base import MasterPipelineContext, MasterPipelineStage
from master_orchestrator.pipeline.progress import ProgressUpdate, ProgressCallbackType
from master_orchestrator.pipeline.stages import (
    DocumentScannerStage,
    DocumentClassifierStage,
    AgentDispatcherStage,
    ResultNormalizerStage,
    CrossValidatorStage,
    OutputGeneratorStage,
)
from master_orchestrator.services.llm_service import LLMService
from master_orchestrator.utils.exceptions import MasterOrchestratorError

logger = structlog.get_logger(__name__)


class MasterOrchestrator:
    """Main orchestrator that coordinates document processing through all stages."""

    def __init__(
        self,
        settings: Settings | None = None,
        llm_service: LLMService | None = None,
        progress_callback: ProgressCallbackType = None,
    ):
        """Initialize the master orchestrator.

        Args:
            settings: Configuration settings. If None, loads from environment.
            llm_service: LLM service for classification. If None, created lazily.
            progress_callback: Optional callback for progress updates.
        """
        self._settings = settings or Settings()
        self._llm_service = llm_service
        self._progress_callback = progress_callback
        self._stages: list[MasterPipelineStage] = []

    def _emit_progress(
        self,
        stage_name: str,
        stage_index: int,
        total_stages: int,
        message: str = "",
        sub_agent: str | None = None,
        current_document: str | None = None,
        processed_documents: int = 0,
        total_documents: int = 0,
    ) -> None:
        """Emit a progress update if callback is registered.

        Args:
            stage_name: Name of the current stage.
            stage_index: Index of the current stage (0-based).
            total_stages: Total number of stages.
            message: Optional progress message.
            sub_agent: Optional sub-agent being processed.
            current_document: Name of document being processed.
            processed_documents: Count of documents completed.
            total_documents: Total documents in batch.
        """
        if self._progress_callback:
            update = ProgressUpdate(
                stage_name=stage_name,
                stage_index=stage_index,
                total_stages=total_stages,
                message=message or f"Processing {stage_name}...",
                sub_agent=sub_agent,
                current_document=current_document,
                processed_documents=processed_documents,
                total_documents=total_documents,
            )
            self._progress_callback(update)

    def process(
        self,
        input_folder: str | Path,
        output_dir: str | Path | None = None,
        output_format: OutputFormat | None = None,
        bank_statement_months: int | None = None,
        financial_threshold: float | None = None,
    ) -> MasterAnalysisResult:
        """Process all documents in a folder.

        Args:
            input_folder: Path to folder containing documents
            output_dir: Optional path to output directory for JSON/Excel files
            output_format: Output format (json, excel, or both)
            bank_statement_months: Optional required bank statement period in months
        Returns:
            MasterAnalysisResult containing all analysis results

        Raises:
            MasterOrchestratorError: If processing fails
        """
        start_time = time.time()
        input_path = Path(input_folder)
        output_path = Path(output_dir) if output_dir else None

        logger.info(
            "starting_master_orchestration",
            input_folder=str(input_path),
            output_dir=str(output_path) if output_path else None,
        )

        # Create context
        context = MasterPipelineContext(
            input_folder=input_path,
            settings=self._settings,
            bank_statement_months=bank_statement_months,
            financial_threshold=financial_threshold,
        )

        # Initialize stages
        self._initialize_stages(output_path, output_format)

        # Execute pipeline
        total_stages = len(self._stages)
        try:
            for i, stage in enumerate(self._stages):
                # Create a bound progress callback for this stage
                def stage_progress_callback(**kwargs):
                    self._emit_progress(
                        stage_name=stage.name,
                        stage_index=i,
                        total_stages=total_stages,
                        **kwargs
                    )
                
                # Inject callback into stage if it supports it
                if hasattr(stage, "set_progress_callback"):
                    stage.set_progress_callback(stage_progress_callback)

                self._emit_progress(
                    stage_name=stage.name,
                    stage_index=i,
                    total_stages=total_stages,
                    message=f"Processing {stage.name}...",
                )
                logger.info("executing_stage", stage=stage.name)
                context = stage.process(context)

        except MasterOrchestratorError:
            # Re-raise orchestrator errors
            raise

        except Exception as e:
            logger.error("pipeline_error", error=str(e), stage=stage.name)
            raise MasterOrchestratorError(
                f"Pipeline failed at stage {stage.name}: {str(e)}",
                {"stage": stage.name, "error": str(e)},
            )

        # Record processing time
        context.processing_time_seconds = time.time() - start_time

        if context.final_result is None:
            raise MasterOrchestratorError("Pipeline completed but no result was generated")

        # Update metadata with final processing time
        context.final_result.metadata.processing_time_seconds = context.processing_time_seconds

        logger.info(
            "master_orchestration_complete",
            duration_seconds=context.processing_time_seconds,
            errors=len(context.errors),
            warnings=len(context.warnings),
        )

        return context.final_result

    def process_with_context(
        self,
        input_folder: str | Path,
        output_dir: str | Path | None = None,
        output_format: OutputFormat | None = None,
        bank_statement_months: int | None = None,
        financial_threshold: float | None = None,
    ) -> tuple[MasterAnalysisResult, MasterPipelineContext]:
        """Process documents and return both result and context.

        This method is useful for debugging or accessing intermediate data.

        Args:
            input_folder: Path to folder containing documents
            output_dir: Optional path to output directory
            output_format: Output format
            bank_statement_months: Optional required bank statement period in months
        Returns:
            Tuple of (MasterAnalysisResult, MasterPipelineContext)
        """
        start_time = time.time()
        input_path = Path(input_folder)
        output_path = Path(output_dir) if output_dir else None

        context = MasterPipelineContext(
            input_folder=input_path,
            settings=self._settings,
            bank_statement_months=bank_statement_months,
            financial_threshold=financial_threshold,
        )

        self._initialize_stages(output_path, output_format)

        total_stages = len(self._stages)
        for i, stage in enumerate(self._stages):
            self._emit_progress(
                stage_name=stage.name,
                stage_index=i,
                total_stages=total_stages,
                message=f"Processing {stage.name}...",
            )
            context = stage.process(context)

        context.processing_time_seconds = time.time() - start_time

        if context.final_result is None:
            raise MasterOrchestratorError("Pipeline completed but no result was generated")

        context.final_result.metadata.processing_time_seconds = context.processing_time_seconds

        return context.final_result, context

    def _initialize_stages(
        self,
        output_dir: Path | None,
        output_format: OutputFormat | None,
    ) -> None:
        """Initialize pipeline stages."""
        self._stages = [
            DocumentScannerStage(),
            DocumentClassifierStage(llm_service=self._llm_service),
            AgentDispatcherStage(),
            ResultNormalizerStage(),
            CrossValidatorStage(),
            OutputGeneratorStage(
                output_dir=output_dir,
                output_format=output_format,
            ),
        ]
