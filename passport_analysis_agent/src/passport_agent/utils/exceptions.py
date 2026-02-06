"""Custom exceptions for the passport analysis agent."""


class PassportAgentError(Exception):
    """Base exception for all passport agent errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class DocumentLoadError(PassportAgentError):
    """Error loading or validating a document."""

    pass


class PreprocessingError(PassportAgentError):
    """Error during image preprocessing."""

    pass


class ExtractionError(PassportAgentError):
    """Error extracting passport data."""

    pass


class MRZParseError(PassportAgentError):
    """Error parsing MRZ data."""

    pass


class ValidationError(PassportAgentError):
    """Error validating passport data."""

    pass


class LLMError(PassportAgentError):
    """Error communicating with the LLM service."""

    pass


class ConfigurationError(PassportAgentError):
    """Error in configuration."""

    pass
