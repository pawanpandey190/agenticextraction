"""Custom exceptions for Master Orchestrator Agent."""

from typing import Any


class MasterOrchestratorError(Exception):
    """Base exception for Master Orchestrator Agent."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DocumentScanError(MasterOrchestratorError):
    """Error during document scanning."""

    pass


class ClassificationError(MasterOrchestratorError):
    """Error during document classification."""

    pass


class AgentDispatchError(MasterOrchestratorError):
    """Error during agent dispatching."""

    pass


class CrossValidationError(MasterOrchestratorError):
    """Error during cross-validation."""

    pass


class OutputGenerationError(MasterOrchestratorError):
    """Error during output generation."""

    pass


class MissingDocumentCategoryError(MasterOrchestratorError):
    """Error when required document categories are missing."""

    def __init__(self, missing_categories: list[str]):
        message = f"Missing required document categories: {', '.join(missing_categories)}"
        super().__init__(message, {"missing_categories": missing_categories})
        self.missing_categories = missing_categories
