"""Unit tests for MRZ service."""

from datetime import date

import pytest

from passport_agent.services.mrz_service import MRZService
from passport_agent.utils.exceptions import MRZParseError


class TestMRZService:
    """Tests for MRZService class."""

    @pytest.fixture
    def service(self) -> MRZService:
        """Create MRZ service instance."""
        return MRZService()

    def test_parse_td3_valid(self, service: MRZService):
        """Test parsing valid TD3 MRZ."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08"

        result = service.parse_td3(line1, line2)

        assert result.document_type == "P"
        assert result.issuing_country == "UTO"
        assert result.last_name == "ERIKSSON"
        assert result.first_name == "ANNA MARIA"
        assert result.passport_number == "L898902C3"
        assert result.nationality == "UTO"
        assert result.date_of_birth == date(1974, 8, 12)
        assert result.sex == "F"
        assert result.expiry_date == date(2012, 4, 15)

    def test_parse_td3_checksums(self, service: MRZService):
        """Test checksum validation."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08"

        result = service.parse_td3(line1, line2)

        # All checksums should be valid for ICAO test passport
        assert result.checksum_results.passport_number is True
        assert result.checksum_results.date_of_birth is True
        assert result.checksum_results.expiry_date is True
        assert result.checksum_results.composite is True
        assert result.checksum_results.all_valid is True

    def test_parse_td3_invalid_passport_checksum(self, service: MRZService):
        """Test detection of invalid passport number checksum."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        # Changed check digit from 6 to 5
        line2 = "L898902C35UTO7408122F1204159<<<<<<<<<<<<<<06"

        result = service.parse_td3(line1, line2)

        assert result.checksum_results.passport_number is False
        assert result.checksum_results.all_valid is False

    def test_parse_td3_invalid_line_length(self, service: MRZService):
        """Test rejection of invalid line length."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA"  # Too short
        line2 = "L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08"

        with pytest.raises(MRZParseError):
            service.parse_td3(line1, line2)

    def test_parse_td3_raw_lines_preserved(self, service: MRZService):
        """Test that raw lines are preserved."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08"

        result = service.parse_td3(line1, line2)

        assert result.raw_line1 == line1
        assert result.raw_line2 == line2

    def test_extract_mrz_lines_from_text(self, service: MRZService):
        """Test MRZ line extraction from OCR text."""
        text = """
        Some header text
        P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
        L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08
        Some footer text
        """

        result = service.extract_mrz_lines(text)

        assert result is not None
        line1, line2 = result
        assert line1.startswith("P<")
        assert len(line1) == 44
        assert len(line2) == 44

    def test_extract_mrz_lines_not_found(self, service: MRZService):
        """Test when MRZ lines are not found."""
        text = "Just some random text without MRZ"

        result = service.extract_mrz_lines(text)

        assert result is None


class TestMRZChecksumCalculation:
    """Tests for detailed checksum calculation."""

    @pytest.fixture
    def service(self) -> MRZService:
        return MRZService()

    def test_composite_checksum_data(self, service: MRZService):
        """Test that composite checksum uses correct data."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08"

        result = service.parse_td3(line1, line2)

        # Composite should include:
        # - Passport number + check (0-9): L898902C36
        # - DOB + check (13-19): 7408122
        # - Expiry + check + personal (21-42): 1204159<<<<<<<<<<<<<<0
        # Check digit at position 43: 6

        assert result.checksum_results.composite is True

    def test_personal_number_handling(self, service: MRZService):
        """Test personal number extraction."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08"

        result = service.parse_td3(line1, line2)

        # Personal number is all fillers, should be None or empty
        assert result.personal_number is None or result.personal_number == ""

    def test_personal_number_with_data(self, service: MRZService):
        """Test personal number when present."""
        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        # Modified to include a personal number (fictional)
        line2 = "L898902C36UTO7408122F12041591234567890123406"

        result = service.parse_td3(line1, line2)

        # Personal number should be extracted
        assert result.personal_number is not None
