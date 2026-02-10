"""Adapter for Financial Document Agent."""

import os
from pathlib import Path
from typing import Any

import structlog

from master_orchestrator.config.settings import Settings
from master_orchestrator.utils.exceptions import AgentDispatchError

logger = structlog.get_logger(__name__)


class FinancialAgentAdapter:
    """Adapter to wrap the financial document agent."""

    def __init__(self, settings: Settings):
        """Initialize the financial agent adapter.

        Args:
            settings: Master orchestrator settings
        """
        self._settings = settings
        self._orchestrator = None

    def _ensure_initialized(self, threshold_eur: float | None = None, required_period_months: int | None = None) -> None:
        """Lazily initialize the financial agent orchestrator.

        Args:
            threshold_eur: Optional override for financial threshold
            required_period_months: Optional required bank statement period in months
        """
        if self._orchestrator is not None:
            return

        try:
            # Set environment variable for financial agent
            api_key = self._settings.get_financial_api_key()
            os.environ["FA_ANTHROPIC_API_KEY"] = api_key or ""

            from financial_agent.config.settings import Settings as FinancialSettings
            from financial_agent.pipeline.orchestrator import PipelineOrchestrator

            financial_settings = FinancialSettings()
            self._orchestrator = PipelineOrchestrator(
                settings=financial_settings,
                threshold_eur=threshold_eur or self._settings.financial_threshold_eur,
                required_period_months=required_period_months,
            )

            logger.info("financial_agent_initialized")

        except ImportError as e:
            raise AgentDispatchError(
                f"Failed to import financial agent: {str(e)}. "
                "Ensure financial-document-agent is installed.",
                {"error": str(e)},
            )
        except Exception as e:
            raise AgentDispatchError(
                f"Failed to initialize financial agent: {str(e)}",
                {"error": str(e)},
            )

    def process(
        self,
        file_path: Path,
        threshold_eur: float | None = None,
        required_period_months: int | None = None,
    ) -> Any:
        """Process a financial document.

        Args:
            file_path: Path to the financial document
            threshold_eur: Optional override for financial threshold
            required_period_months: Optional required bank statement period in months

        Returns:
            AnalysisResult from the financial agent
        """
        self._ensure_initialized(threshold_eur, required_period_months)

        logger.info("processing_financial", file=str(file_path))

        try:
            result = self._orchestrator.process(str(file_path))
            logger.info(
                "financial_processed",
                file=str(file_path),
                document_type=getattr(result, "document_type", None),
            )
            return result

        except Exception as e:
            logger.error("financial_processing_error", file=str(file_path), error=str(e))
            raise AgentDispatchError(
                f"Financial agent processing failed: {str(e)}",
                {"file": str(file_path), "error": str(e)},
            )
