"""Output Generator Stage - Generates JSON and Excel output."""

import json
from pathlib import Path

import structlog

from master_orchestrator.config.constants import OutputFormat
from master_orchestrator.models.unified_result import MasterAnalysisResult
from master_orchestrator.pipeline.base import MasterPipelineContext, MasterPipelineStage
from master_orchestrator.services.excel_service import ExcelService
from master_orchestrator.utils.exceptions import OutputGenerationError

logger = structlog.get_logger(__name__)


class OutputGeneratorStage(MasterPipelineStage):
    """Stage 6: Generate output files (JSON and/or Excel)."""

    def __init__(
        self,
        output_dir: Path | None = None,
        output_format: OutputFormat | None = None,
        excel_service: ExcelService | None = None,
    ):
        self._output_dir = output_dir
        self._output_format = output_format
        self._excel_service = excel_service

    @property
    def name(self) -> str:
        return "OutputGenerator"

    def process(self, context: MasterPipelineContext) -> MasterPipelineContext:
        """Assemble final result and generate output files."""
        logger.info("generating_output")

        # Assemble final result
        context.final_result = MasterAnalysisResult(
            passport_details=context.passport_details,
            education_summary=context.education_summary,
            financial_summary=context.financial_summary,
            cross_validation=context.cross_validation,
            metadata=context.get_metadata(),
        )

        # Determine output format
        output_format = self._output_format or context.settings.output_format

        # Generate output files if output directory is specified
        if self._output_dir is not None:
            self._output_dir.mkdir(parents=True, exist_ok=True)

            if output_format in (OutputFormat.JSON, OutputFormat.BOTH):
                self._generate_json(context)

            if output_format in (OutputFormat.EXCEL, OutputFormat.BOTH):
                self._generate_excel(context)

        logger.info(
            "output_generation_complete",
            format=output_format.value,
            output_dir=str(self._output_dir) if self._output_dir else None,
        )

        return context

    def _generate_json(self, context: MasterPipelineContext) -> None:
        """Generate JSON output file."""
        if context.final_result is None or self._output_dir is None:
            return

        try:
            output_path = self._output_dir / "analysis_result.json"
            output_data = context.final_result.to_output_dict()

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)

            logger.info("json_output_generated", path=str(output_path))

        except Exception as e:
            error_msg = f"Failed to generate JSON output: {str(e)}"
            logger.error("json_generation_error", error=str(e))
            context.add_error(error_msg)
            raise OutputGenerationError(error_msg)

    def _generate_excel(self, context: MasterPipelineContext) -> None:
        """Generate Excel output file."""
        if context.final_result is None or self._output_dir is None:
            return

        try:
            if self._excel_service is None:
                self._excel_service = ExcelService()

            output_path = self._output_dir / "analysis_result.xlsx"
            self._excel_service.generate(context.final_result, output_path)

            logger.info("excel_output_generated", path=str(output_path))

        except Exception as e:
            error_msg = f"Failed to generate Excel output: {str(e)}"
            logger.error("excel_generation_error", error=str(e))
            context.add_error(error_msg)
            raise OutputGenerationError(error_msg)
