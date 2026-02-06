"""Prompts module for education credential agent."""

from .classification import CLASSIFICATION_PROMPT, CLASSIFICATION_WITH_IMAGE_PROMPT
from .extraction import EXTRACTION_PROMPT
from .system import OCR_SYSTEM_PROMPT, SYSTEM_PROMPT

__all__ = [
    "CLASSIFICATION_PROMPT",
    "CLASSIFICATION_WITH_IMAGE_PROMPT",
    "EXTRACTION_PROMPT",
    "OCR_SYSTEM_PROMPT",
    "SYSTEM_PROMPT",
]
