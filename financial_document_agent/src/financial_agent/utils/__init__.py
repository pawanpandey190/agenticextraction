"""Utility functions and classes."""

from .exceptions import (
    ClassificationError,
    CurrencyConversionError,
    DocumentLoadError,
    ExtractionError,
    FinancialAgentError,
    OCRError,
)
from .image_utils import encode_image_base64, resize_image_if_needed
from .pdf_utils import pdf_to_images

__all__ = [
    "FinancialAgentError",
    "DocumentLoadError",
    "OCRError",
    "ClassificationError",
    "ExtractionError",
    "CurrencyConversionError",
    "encode_image_base64",
    "resize_image_if_needed",
    "pdf_to_images",
]
