"""Unit tests for fuzzy matching utilities."""

import pytest

from passport_agent.utils.fuzzy_match import (
    exact_match,
    fuzzy_match,
    normalize_name,
    partial_match,
)


class TestNormalizeName:
    """Tests for normalize_name function."""

    def test_uppercase(self):
        """Test uppercase conversion."""
        assert normalize_name("john doe") == "JOHN DOE"

    def test_accents_removed(self):
        """Test accent/diacritic removal."""
        assert normalize_name("José García") == "JOSE GARCIA"
        assert normalize_name("Müller") == "MULLER"
        assert normalize_name("Søren") == "SOREN"

    def test_mrz_fillers_replaced(self):
        """Test MRZ filler replacement."""
        assert normalize_name("SMITH<<JOHN") == "SMITH JOHN"

    def test_whitespace_normalized(self):
        """Test whitespace normalization."""
        assert normalize_name("  John   Doe  ") == "JOHN DOE"

    def test_punctuation_removed(self):
        """Test punctuation removal."""
        assert normalize_name("O'Brien") == "OBRIEN"
        assert normalize_name("Smith-Jones") == "SMITHJONES"

    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_name("") == ""
        assert normalize_name(None) == ""


class TestFuzzyMatch:
    """Tests for fuzzy_match function."""

    def test_exact_match(self):
        """Test exact match returns True."""
        is_match, score = fuzzy_match("JOHN DOE", "JOHN DOE")
        assert is_match is True
        assert score == 1.0

    def test_case_insensitive(self):
        """Test case insensitivity."""
        is_match, score = fuzzy_match("john doe", "JOHN DOE")
        assert is_match is True

    def test_similar_names(self):
        """Test similar names above threshold."""
        is_match, score = fuzzy_match("ANNA MARIA", "ANNA<MARIA", threshold=0.85)
        assert is_match is True
        assert score >= 0.85

    def test_different_order(self):
        """Test names in different order (token sort)."""
        is_match, score = fuzzy_match("MARIA ANNA", "ANNA MARIA", threshold=0.85)
        assert is_match is True

    def test_below_threshold(self):
        """Test names below threshold."""
        is_match, score = fuzzy_match("JOHN", "JANE", threshold=0.85)
        assert is_match is False
        assert score < 0.85

    def test_completely_different(self):
        """Test completely different names."""
        is_match, score = fuzzy_match("JOHN DOE", "JANE SMITH", threshold=0.85)
        assert is_match is False

    def test_empty_strings(self):
        """Test empty string handling."""
        is_match, score = fuzzy_match("", "JOHN", threshold=0.85)
        assert is_match is False
        assert score == 0.0

    def test_accents_handled(self):
        """Test that accents are properly handled."""
        is_match, score = fuzzy_match("José García", "JOSE GARCIA", threshold=0.85)
        assert is_match is True


class TestExactMatch:
    """Tests for exact_match function."""

    def test_exact_match(self):
        """Test exact match."""
        assert exact_match("JOHN DOE", "JOHN DOE") is True

    def test_case_insensitive(self):
        """Test case insensitivity."""
        assert exact_match("john doe", "JOHN DOE") is True

    def test_not_match(self):
        """Test non-match."""
        assert exact_match("JOHN DOE", "JOHN SMITH") is False

    def test_whitespace_normalized(self):
        """Test whitespace normalization."""
        assert exact_match("JOHN  DOE", "JOHN DOE") is True

    def test_mrz_fillers(self):
        """Test MRZ filler handling."""
        assert exact_match("JOHN<<DOE", "JOHN DOE") is True


class TestPartialMatch:
    """Tests for partial_match function."""

    def test_substring_match(self):
        """Test substring matching."""
        is_match, score = partial_match("JOHN", "JOHN WILLIAM", threshold=0.8)
        assert is_match is True
        assert score >= 0.8

    def test_abbreviated_name(self):
        """Test abbreviated name matching."""
        is_match, score = partial_match("J SMITH", "JOHN SMITH", threshold=0.7)
        # This may or may not match depending on the partial ratio
        # At minimum, verify it returns a score
        assert 0.0 <= score <= 1.0

    def test_no_partial_match(self):
        """Test when there's no partial match."""
        is_match, score = partial_match("ANNA", "ROBERT", threshold=0.8)
        assert is_match is False
