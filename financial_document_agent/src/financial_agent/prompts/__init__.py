"""Prompt templates for LLM interactions."""

from .classification import CLASSIFICATION_PROMPT
from .extraction import get_extraction_prompt
from .system import SYSTEM_PROMPT

__all__ = ["SYSTEM_PROMPT", "CLASSIFICATION_PROMPT", "get_extraction_prompt"]
