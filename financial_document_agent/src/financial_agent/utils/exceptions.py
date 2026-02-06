"""Custom exceptions for the financial agent."""


class FinancialAgentError(Exception):
    """Base exception for all financial agent errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class DocumentLoadError(FinancialAgentError):
    """Error loading or validating a document."""

    pass


class OCRError(FinancialAgentError):
    """Error during OCR processing."""

    pass


class ClassificationError(FinancialAgentError):
    """Error classifying a document."""

    pass


class ExtractionError(FinancialAgentError):
    """Error extracting financial data."""

    pass


class CurrencyConversionError(FinancialAgentError):
    """Error converting currency."""

    pass


class LLMError(FinancialAgentError):
    """Error communicating with the LLM service."""

    pass


class ConfigurationError(FinancialAgentError):
    """Error in configuration."""

    pass
