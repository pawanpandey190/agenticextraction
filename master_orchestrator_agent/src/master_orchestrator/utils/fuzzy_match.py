"""Fuzzy matching utilities for name and date comparison."""

import re
from datetime import date, datetime

from rapidfuzz import fuzz


def normalize_name(name: str | None) -> str:
    """Normalize a name for comparison.

    - Convert to uppercase
    - Remove extra whitespace
    - Remove common titles and suffixes
    - Remove punctuation
    """
    if not name:
        return ""

    # Convert to uppercase
    normalized = name.upper()

    # Remove common titles
    titles = [
        "MR", "MRS", "MS", "MISS", "DR", "PROF", "SIR", "MADAM",
        "MR.", "MRS.", "MS.", "MISS.", "DR.", "PROF.",
    ]
    for title in titles:
        normalized = re.sub(rf"\b{title}\b\.?\s*", "", normalized)

    # Remove punctuation except spaces
    normalized = re.sub(r"[^\w\s]", "", normalized)

    # Normalize whitespace
    normalized = " ".join(normalized.split())

    return normalized.strip()


def fuzzy_match_names(
    name1: str | None,
    name2: str | None,
    threshold: float = 0.85,
) -> tuple[bool, float]:
    """Compare two names using fuzzy matching.

    Args:
        name1: First name to compare
        name2: Second name to compare
        threshold: Minimum score (0-1) to consider a match

    Returns:
        Tuple of (is_match, score)
    """
    if not name1 or not name2:
        return False, 0.0

    # Normalize names
    norm1 = normalize_name(name1)
    norm2 = normalize_name(name2)

    if not norm1 or not norm2:
        return False, 0.0

    # Calculate similarity using token sort ratio
    # This handles name order differences (e.g., "John Smith" vs "Smith John")
    score = fuzz.token_sort_ratio(norm1, norm2) / 100.0

    return score >= threshold, score


def compare_dates(
    date1: str | date | None,
    date2: str | date | None,
) -> tuple[bool, str | None, str | None]:
    """Compare two dates.

    Args:
        date1: First date (string in ISO format or date object)
        date2: Second date (string in ISO format or date object)

    Returns:
        Tuple of (is_match, date1_str, date2_str)
    """
    if date1 is None or date2 is None:
        return False, _date_to_str(date1), _date_to_str(date2)

    # Convert to date objects for comparison
    d1 = _parse_date(date1)
    d2 = _parse_date(date2)

    if d1 is None or d2 is None:
        return False, _date_to_str(date1), _date_to_str(date2)

    return d1 == d2, d1.isoformat(), d2.isoformat()


def _parse_date(value: str | date) -> date | None:
    """Parse a date from string or return as-is if already a date."""
    if isinstance(value, date):
        return value

    if isinstance(value, str):
        # Try common date formats
        formats = [
            "%Y-%m-%d",  # ISO format
            "%d/%m/%Y",  # European format
            "%m/%d/%Y",  # US format
            "%d-%m-%Y",
            "%Y/%m/%d",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

    return None


def _date_to_str(value: str | date | None) -> str | None:
    """Convert date to string."""
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    return str(value)
