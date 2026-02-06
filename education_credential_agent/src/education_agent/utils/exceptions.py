"""Custom exceptions for the education credential agent."""

from typing import Any


class EducationAgentError(Exception):
    """Base exception for all education agent errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class DocumentLoadError(EducationAgentError):
    """Error loading or validating a document."""

    pass


class OCRError(EducationAgentError):
    """Error during OCR processing."""

    pass


class ClassificationError(EducationAgentError):
    """Error classifying a document."""

    pass


class ExtractionError(EducationAgentError):
    """Error extracting credential data."""

    pass


class GradeConversionError(EducationAgentError):
    """Error converting grade to French scale."""

    pass


class ValidationError(EducationAgentError):
    """Error validating credential data (e.g., semester validation)."""

    pass


class LLMError(EducationAgentError):
    """Error communicating with the LLM service."""

    pass


class ConfigurationError(EducationAgentError):
    """Error in configuration."""

    pass
