"""Fuzzy string matching utilities for name comparison."""

import re
import unicodedata

from rapidfuzz import fuzz


def normalize_name(name: str) -> str:
    """Normalize a name for comparison.

    - Converts to uppercase
    - Removes accents/diacritics
    - Normalizes whitespace
    - Removes punctuation

    Args:
        name: Raw name string

    Returns:
        Normalized name
    """
    if not name:
        return ""

    # Convert to uppercase
    normalized = name.upper()

    # Handle special Scandinavian/Nordic characters that don't decompose with NFD
    special_chars = {
        "Ø": "O",
        "Æ": "AE",
        "Ð": "D",
        "Þ": "TH",
        "Ł": "L",
        "Đ": "D",
    }
    for char, replacement in special_chars.items():
        normalized = normalized.replace(char, replacement)

    # Remove accents/diacritics using NFD normalization
    normalized = "".join(
        c
        for c in unicodedata.normalize("NFD", normalized)
        if unicodedata.category(c) != "Mn"
    )

    # Replace MRZ filler characters
    normalized = normalized.replace("<", " ")

    # Remove punctuation except spaces
    normalized = re.sub(r"[^\w\s]", "", normalized)

    # Normalize whitespace
    normalized = " ".join(normalized.split())

    return normalized


def fuzzy_match(str1: str, str2: str, threshold: float = 0.85) -> tuple[bool, float]:
    """Compare two strings using fuzzy matching.

    Uses token sort ratio which handles different word orders.

    Args:
        str1: First string
        str2: Second string
        threshold: Minimum similarity ratio (0.0-1.0)

    Returns:
        Tuple of (is_match, similarity_ratio)
    """
    # Normalize both strings
    norm1 = normalize_name(str1)
    norm2 = normalize_name(str2)

    if not norm1 or not norm2:
        return False, 0.0

    # Exact match check first
    if norm1 == norm2:
        return True, 1.0

    # Use token sort ratio for better handling of name variations
    # This handles cases like "ANNA MARIA" vs "MARIA ANNA"
    ratio = fuzz.token_sort_ratio(norm1, norm2) / 100.0

    return ratio >= threshold, ratio


def exact_match(str1: str, str2: str) -> bool:
    """Compare two strings for exact match after normalization.

    Args:
        str1: First string
        str2: Second string

    Returns:
        True if strings match exactly after normalization
    """
    norm1 = normalize_name(str1)
    norm2 = normalize_name(str2)

    return norm1 == norm2


def partial_match(str1: str, str2: str, threshold: float = 0.8) -> tuple[bool, float]:
    """Check if one string partially contains the other.

    Useful for matching when one source has abbreviated names.

    Args:
        str1: First string
        str2: Second string
        threshold: Minimum similarity ratio

    Returns:
        Tuple of (is_match, similarity_ratio)
    """
    norm1 = normalize_name(str1)
    norm2 = normalize_name(str2)

    if not norm1 or not norm2:
        return False, 0.0

    # Check if one is substring of the other
    if norm1 in norm2 or norm2 in norm1:
        return True, 0.95

    # Use partial ratio for partial matching
    ratio = fuzz.partial_ratio(norm1, norm2) / 100.0

    return ratio >= threshold, ratio
