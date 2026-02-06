"""Unit tests for MRZ utility functions."""

from datetime import date

import pytest

from passport_agent.utils.mrz_utils import (
    calculate_check_digit,
    format_date_to_mrz,
    normalize_passport_number,
    parse_mrz_date,
    parse_name_field,
    sex_from_mrz,
    validate_check_digit,
)
from passport_agent.utils.exceptions import MRZParseError


class TestCalculateCheckDigit:
    """Tests for calculate_check_digit function."""

    def test_simple_digits(self):
        """Test check digit calculation with simple digits."""
        # Example from ICAO 9303
        assert calculate_check_digit("520727") == "3"

    def test_alphanumeric(self):
        """Test check digit with alphanumeric data."""
        # L898902C3 should have check digit 6
        assert calculate_check_digit("L898902C3") == "6"

    def test_with_fillers(self):
        """Test check digit with filler characters."""
        # All fillers should be 0
        assert calculate_check_digit("<<<<<<") == "0"

    def test_passport_number_example(self):
        """Test ICAO example passport number."""
        # From ICAO test passport
        assert calculate_check_digit("L898902C3") == "6"

    def test_date_of_birth_example(self):
        """Test date of birth check digit."""
        # 740812 should have check digit 2
        assert calculate_check_digit("740812") == "2"

    def test_expiry_date_example(self):
        """Test expiry date check digit."""
        # 120415 should have check digit 9
        assert calculate_check_digit("120415") == "9"

    def test_invalid_character_raises(self):
        """Test that invalid characters raise error."""
        with pytest.raises(MRZParseError):
            calculate_check_digit("ABC@123")


class TestValidateCheckDigit:
    """Tests for validate_check_digit function."""

    def test_valid_check_digit(self):
        """Test valid check digit validation."""
        assert validate_check_digit("L898902C3", "6") is True

    def test_invalid_check_digit(self):
        """Test invalid check digit validation."""
        assert validate_check_digit("L898902C3", "5") is False

    def test_date_validation(self):
        """Test date check digit validation."""
        assert validate_check_digit("740812", "2") is True
        assert validate_check_digit("740812", "1") is False


class TestParseMrzDate:
    """Tests for parse_mrz_date function."""

    def test_birth_date_1900s(self):
        """Test birth date in 1900s (year >= 30)."""
        result = parse_mrz_date("740812", is_expiry=False)
        assert result == date(1974, 8, 12)

    def test_birth_date_2000s(self):
        """Test birth date in 2000s (year < 30)."""
        result = parse_mrz_date("150615", is_expiry=False)
        assert result == date(2015, 6, 15)

    def test_expiry_date_2000s(self):
        """Test expiry date in 2000s (year < 80)."""
        result = parse_mrz_date("250115", is_expiry=True)
        assert result == date(2025, 1, 15)

    def test_expiry_date_1900s(self):
        """Test expiry date in 1900s (year >= 80)."""
        result = parse_mrz_date("990101", is_expiry=True)
        assert result == date(1999, 1, 1)

    def test_invalid_length_raises(self):
        """Test that invalid length raises error."""
        with pytest.raises(MRZParseError):
            parse_mrz_date("12345")

    def test_invalid_date_raises(self):
        """Test that invalid date raises error."""
        with pytest.raises(MRZParseError):
            parse_mrz_date("999999")


class TestFormatDateToMrz:
    """Tests for format_date_to_mrz function."""

    def test_format_date(self):
        """Test date formatting to MRZ."""
        assert format_date_to_mrz(date(1974, 8, 12)) == "740812"

    def test_format_date_with_padding(self):
        """Test date formatting with zero padding."""
        assert format_date_to_mrz(date(2005, 1, 5)) == "050105"


class TestParseNameField:
    """Tests for parse_name_field function."""

    def test_simple_name(self):
        """Test simple surname and given name."""
        last, first = parse_name_field("ERIKSSON<<ANNA<<<<<<<<<<<<<<<<<<<<<")
        assert last == "ERIKSSON"
        assert first == "ANNA"

    def test_multiple_given_names(self):
        """Test multiple given names."""
        last, first = parse_name_field("ERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<")
        assert last == "ERIKSSON"
        assert first == "ANNA MARIA"

    def test_compound_surname(self):
        """Test compound surname with filler."""
        last, first = parse_name_field("DE<GROOT<<JAN<<<<<<<<<<<<<<<<<<<<<<<")
        assert last == "DE GROOT"
        assert first == "JAN"

    def test_only_surname(self):
        """Test name with only surname (no given names)."""
        last, first = parse_name_field("SMITH<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        assert last == "SMITH"
        assert first == ""


class TestNormalizePassportNumber:
    """Tests for normalize_passport_number function."""

    def test_with_fillers(self):
        """Test removing filler characters."""
        assert normalize_passport_number("L898902C3<") == "L898902C3"

    def test_lowercase(self):
        """Test uppercase conversion."""
        assert normalize_passport_number("l898902c3") == "L898902C3"

    def test_with_spaces(self):
        """Test removing spaces."""
        assert normalize_passport_number("L898 902C3") == "L898902C3"


class TestSexFromMrz:
    """Tests for sex_from_mrz function."""

    def test_male(self):
        """Test male sex."""
        assert sex_from_mrz("M") == "M"

    def test_female(self):
        """Test female sex."""
        assert sex_from_mrz("F") == "F"

    def test_unspecified(self):
        """Test unspecified sex."""
        assert sex_from_mrz("<") == "X"

    def test_other(self):
        """Test other values default to unspecified."""
        assert sex_from_mrz("X") == "X"
