"""Unit tests for fuzzy matching utilities."""

import pytest
from datetime import date

from master_orchestrator.utils.fuzzy_match import (
    normalize_name,
    fuzzy_match_names,
    compare_dates,
)


class TestNormalizeName:
    """Tests for normalize_name function."""

    def test_normalize_basic(self):
        """Test basic normalization."""
        assert normalize_name("John Doe") == "JOHN DOE"

    def test_normalize_extra_whitespace(self):
        """Test normalization removes extra whitespace."""
        assert normalize_name("John   Doe") == "JOHN DOE"
        assert normalize_name("  John Doe  ") == "JOHN DOE"

    def test_normalize_removes_titles(self):
        """Test normalization removes common titles."""
        assert normalize_name("Mr. John Doe") == "JOHN DOE"
        assert normalize_name("Dr. John Doe") == "JOHN DOE"
        assert normalize_name("Mrs. Jane Doe") == "JANE DOE"

    def test_normalize_removes_punctuation(self):
        """Test normalization removes punctuation."""
        assert normalize_name("O'Brien") == "OBRIEN"
        assert normalize_name("Jean-Pierre") == "JEANPIERRE"

    def test_normalize_empty(self):
        """Test normalization of empty/None."""
        assert normalize_name("") == ""
        assert normalize_name(None) == ""


class TestFuzzyMatchNames:
    """Tests for fuzzy_match_names function."""

    def test_exact_match(self):
        """Test exact name match."""
        is_match, score = fuzzy_match_names("John Doe", "John Doe")
        assert is_match is True
        assert score == 1.0

    def test_case_insensitive_match(self):
        """Test case insensitive matching."""
        is_match, score = fuzzy_match_names("john doe", "JOHN DOE")
        assert is_match is True
        assert score == 1.0

    def test_name_order_match(self):
        """Test matching with different name order."""
        is_match, score = fuzzy_match_names("John Doe", "Doe John")
        assert is_match is True
        assert score >= 0.85

    def test_similar_names_match(self):
        """Test matching similar names (OCR variations)."""
        is_match, score = fuzzy_match_names("John Doe", "Jonn Doe")
        assert is_match is True
        assert score >= 0.85

    def test_different_names_no_match(self):
        """Test non-matching different names."""
        is_match, score = fuzzy_match_names("John Doe", "Jane Smith")
        assert is_match is False
        assert score < 0.85

    def test_empty_names(self):
        """Test with empty/None names."""
        is_match, score = fuzzy_match_names("", "John Doe")
        assert is_match is False
        assert score == 0.0

        is_match, score = fuzzy_match_names(None, "John Doe")
        assert is_match is False
        assert score == 0.0

    def test_custom_threshold(self):
        """Test with custom threshold."""
        # Similar names that would match at 0.85 but not at 0.95
        is_match_low, score = fuzzy_match_names("John Doe", "Jon Doe", threshold=0.7)
        is_match_high, _ = fuzzy_match_names("John Doe", "Jon Doe", threshold=0.99)

        assert is_match_low is True
        assert is_match_high is False


class TestCompareDates:
    """Tests for compare_dates function."""

    def test_matching_iso_dates(self):
        """Test matching ISO format dates."""
        is_match, d1, d2 = compare_dates("1990-01-15", "1990-01-15")
        assert is_match is True
        assert d1 == "1990-01-15"
        assert d2 == "1990-01-15"

    def test_matching_date_objects(self):
        """Test matching date objects."""
        is_match, d1, d2 = compare_dates(
            date(1990, 1, 15),
            date(1990, 1, 15),
        )
        assert is_match is True

    def test_mixed_date_formats(self):
        """Test matching mixed formats."""
        is_match, d1, d2 = compare_dates(
            "1990-01-15",
            date(1990, 1, 15),
        )
        assert is_match is True

    def test_non_matching_dates(self):
        """Test non-matching dates."""
        is_match, d1, d2 = compare_dates("1990-01-15", "1991-01-15")
        assert is_match is False

    def test_none_dates(self):
        """Test with None dates."""
        is_match, d1, d2 = compare_dates(None, "1990-01-15")
        assert is_match is False
        assert d1 is None

        is_match, d1, d2 = compare_dates("1990-01-15", None)
        assert is_match is False
        assert d2 is None

    def test_european_date_format(self):
        """Test European date format."""
        is_match, d1, d2 = compare_dates("15/01/1990", "1990-01-15")
        assert is_match is True

    def test_us_date_format(self):
        """Test US date format."""
        is_match, d1, d2 = compare_dates("01/15/1990", "1990-01-15")
        assert is_match is True
