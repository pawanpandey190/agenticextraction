"""Prompts for passport analysis."""

from .extraction import get_mrz_extraction_prompt, get_visual_extraction_prompt
from .system import MRZ_EXTRACTION_SYSTEM_PROMPT, VISUAL_EXTRACTION_SYSTEM_PROMPT

__all__ = [
    "MRZ_EXTRACTION_SYSTEM_PROMPT",
    "VISUAL_EXTRACTION_SYSTEM_PROMPT",
    "get_mrz_extraction_prompt",
    "get_visual_extraction_prompt",
]
