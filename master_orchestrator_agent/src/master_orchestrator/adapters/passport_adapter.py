"""Adapter for Passport Analysis Agent."""

import os
from pathlib import Path
from typing import Any

import structlog

from master_orchestrator.config.settings import Settings
from master_orchestrator.utils.exceptions import AgentDispatchError

logger = structlog.get_logger(__name__)


class PassportAgentAdapter:
    """Adapter to wrap the passport analysis agent."""

    def __init__(self, settings: Settings):
        """Initialize the passport agent adapter.

        Args:
            settings: Master orchestrator settings
        """
        self._settings = settings
        self._orchestrator = None

    def _ensure_initialized(self) -> None:
        """Lazily initialize the passport agent orchestrator."""
        if self._orchestrator is not None:
            return

        try:
            # Set environment variable for passport agent
            api_key = self._settings.get_passport_api_key()
            os.environ["PA_OPENAI_API_KEY"] = api_key

            from passport_agent.config.settings import Settings as PassportSettings
            from passport_agent.pipeline.orchestrator import PassportPipelineOrchestrator

            passport_settings = PassportSettings()
            self._orchestrator = PassportPipelineOrchestrator(settings=passport_settings)

            logger.info("passport_agent_initialized")

        except ImportError as e:
            raise AgentDispatchError(
                f"Failed to import passport agent: {str(e)}. "
                "Ensure passport-analysis-agent is installed.",
                {"error": str(e)},
            )
        except Exception as e:
            raise AgentDispatchError(
                f"Failed to initialize passport agent: {str(e)}",
                {"error": str(e)},
            )

    def process(self, file_path: Path) -> Any:
        """Process a passport document.

        Args:
            file_path: Path to the passport document

        Returns:
            PassportAnalysisResult from the passport agent
        """
        self._ensure_initialized()

        logger.info("processing_passport", file=str(file_path))

        try:
            result = self._orchestrator.process(str(file_path))
            logger.info(
                "passport_processed",
                file=str(file_path),
                accuracy_score=getattr(result, "accuracy_score", None),
            )
            return result

        except Exception as e:
            logger.error("passport_processing_error", file=str(file_path), error=str(e))
            raise AgentDispatchError(
                f"Passport agent processing failed: {str(e)}",
                {"file": str(file_path), "error": str(e)},
            )
