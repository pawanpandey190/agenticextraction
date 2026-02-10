"""Adapter for Education Credential Agent."""

import os
from pathlib import Path
from typing import Any

import structlog

from master_orchestrator.config.settings import Settings
from master_orchestrator.utils.exceptions import AgentDispatchError

logger = structlog.get_logger(__name__)


class EducationAgentAdapter:
    """Adapter to wrap the education credential agent."""

    def __init__(self, settings: Settings):
        """Initialize the education agent adapter.

        Args:
            settings: Master orchestrator settings
        """
        self._settings = settings
        self._orchestrator = None

    def _ensure_initialized(self, grade_table_path: str | None = None) -> None:
        """Lazily initialize the education agent orchestrator.

        Args:
            grade_table_path: Optional path to grade conversion table
        """
        if self._orchestrator is not None:
            return

        try:
            # Set environment variable for education agent
            api_key = self._settings.get_education_api_key()
            os.environ["EA_ANTHROPIC_API_KEY"] = api_key or ""

            from education_agent.config.settings import Settings as EducationSettings
            from education_agent.pipeline.orchestrator import PipelineOrchestrator

            education_settings = EducationSettings()
            self._orchestrator = PipelineOrchestrator(
                settings=education_settings,
                grade_table_path=grade_table_path,
            )

            logger.info("education_agent_initialized")

        except ImportError as e:
            raise AgentDispatchError(
                f"Failed to import education agent: {str(e)}. "
                "Ensure education-credential-agent is installed.",
                {"error": str(e)},
            )
        except Exception as e:
            raise AgentDispatchError(
                f"Failed to initialize education agent: {str(e)}",
                {"error": str(e)},
            )

    def process(
        self,
        file_paths: list[Path],
        grade_table_path: str | None = None,
    ) -> Any:
        """Process education documents.

        Args:
            file_paths: List of paths to education documents
            grade_table_path: Optional path to grade conversion table

        Returns:
            AnalysisResult from the education agent
        """
        self._ensure_initialized(grade_table_path)

        logger.info("processing_education", file_count=len(file_paths))

        try:
            # Convert paths to strings for the education agent
            str_paths = [str(p) for p in file_paths]
            result = self._orchestrator.process_files(str_paths)

            logger.info(
                "education_processed",
                file_count=len(file_paths),
                highest_qual=getattr(
                    getattr(result, "highest_qualification", None),
                    "qualification_name",
                    None,
                ),
            )
            return result

        except Exception as e:
            logger.error(
                "education_processing_error",
                file_count=len(file_paths),
                error=str(e),
            )
            raise AgentDispatchError(
                f"Education agent processing failed: {str(e)}",
                {"file_count": len(file_paths), "error": str(e)},
            )

    def process_folder(
        self,
        folder_path: Path,
        grade_table_path: str | None = None,
    ) -> Any:
        """Process all education documents in a folder.

        Args:
            folder_path: Path to folder containing education documents
            grade_table_path: Optional path to grade conversion table

        Returns:
            AnalysisResult from the education agent
        """
        self._ensure_initialized(grade_table_path)

        logger.info("processing_education_folder", folder=str(folder_path))

        try:
            result = self._orchestrator.process_folder(str(folder_path))

            logger.info(
                "education_folder_processed",
                folder=str(folder_path),
            )
            return result

        except Exception as e:
            logger.error(
                "education_folder_processing_error",
                folder=str(folder_path),
                error=str(e),
            )
            raise AgentDispatchError(
                f"Education agent folder processing failed: {str(e)}",
                {"folder": str(folder_path), "error": str(e)},
            )
