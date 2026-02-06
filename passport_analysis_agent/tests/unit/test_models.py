"""Unit tests for data models."""

from datetime import date

import pytest

from passport_agent.models.mrz import MRZChecksumResult, MRZData
from passport_agent.models.passport_data import VisualPassportData
from passport_agent.models.result import PassportAnalysisResult
from passport_agent.models.validation import CrossValidationResult, FieldComparison


class TestVisualPassportData:
    """Tests for VisualPassportData model."""

    def test_name_uppercase(self):
        """Test that names are converted to uppercase."""
        data = VisualPassportData(
            first_name="john william",
            last_name="smith",
        )
        assert data.first_name == "JOHN WILLIAM"
        assert data.last_name == "SMITH"

    def test_passport_number_normalized(self):
        """Test passport number normalization."""
        data = VisualPassportData(passport_number="ab 123 456")
        assert data.passport_number == "AB123456"

    def test_sex_normalization(self):
        """Test sex field normalization."""
        assert VisualPassportData(sex="male").sex == "M"
        assert VisualPassportData(sex="Female").sex == "F"
        assert VisualPassportData(sex="other").sex == "X"

    def test_country_code_uppercase(self):
        """Test country code uppercase."""
        data = VisualPassportData(issuing_country="usa", nationality="gbr")
        assert data.issuing_country == "USA"
        assert data.nationality == "GBR"

    def test_has_required_fields_true(self):
        """Test has_required_fields when all present."""
        data = VisualPassportData(
            first_name="JOHN",
            last_name="DOE",
            date_of_birth=date(1990, 1, 1),
            passport_number="123456789",
        )
        assert data.has_required_fields() is True

    def test_has_required_fields_false(self):
        """Test has_required_fields when missing."""
        data = VisualPassportData(
            first_name="JOHN",
            last_name="DOE",
        )
        assert data.has_required_fields() is False


class TestMRZChecksumResult:
    """Tests for MRZChecksumResult model."""

    def test_all_valid(self):
        """Test all_valid property."""
        result = MRZChecksumResult(
            passport_number=True,
            date_of_birth=True,
            expiry_date=True,
            composite=True,
        )
        assert result.all_valid is True

    def test_not_all_valid(self):
        """Test all_valid when one is false."""
        result = MRZChecksumResult(
            passport_number=True,
            date_of_birth=False,
            expiry_date=True,
            composite=True,
        )
        assert result.all_valid is False

    def test_valid_count(self):
        """Test valid_count property."""
        result = MRZChecksumResult(
            passport_number=True,
            date_of_birth=False,
            expiry_date=True,
            composite=False,
        )
        assert result.valid_count == 2

    def test_to_dict(self):
        """Test to_dict conversion."""
        result = MRZChecksumResult(
            passport_number=True,
            date_of_birth=True,
            expiry_date=True,
            composite=True,
        )
        d = result.to_dict()
        assert d == {
            "passport_number": True,
            "date_of_birth": True,
            "expiry_date": True,
            "composite": True,
        }


class TestMRZData:
    """Tests for MRZData model."""

    def test_full_name_property(self):
        """Test full_name property."""
        data = MRZData(
            document_type="P",
            issuing_country="UTO",
            last_name="ERIKSSON",
            first_name="ANNA MARIA",
            passport_number="L898902C3",
            nationality="UTO",
            date_of_birth=date(1974, 8, 12),
            sex="F",
            expiry_date=date(2012, 4, 15),
            raw_line1="P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<",
            raw_line2="L898902C36UTO7408122F1204159<<<<<<<<<<<<<<06",
        )
        assert data.full_name == "ANNA MARIA ERIKSSON"

    def test_sex_normalization(self):
        """Test sex field normalization from MRZ."""
        data = MRZData(
            document_type="P",
            issuing_country="UTO",
            last_name="DOE",
            first_name="JOHN",
            passport_number="123456789",
            nationality="UTO",
            date_of_birth=date(1990, 1, 1),
            sex="<",  # MRZ filler for unspecified
            expiry_date=date(2030, 1, 1),
            raw_line1="X" * 44,
            raw_line2="X" * 44,
        )
        assert data.sex == "X"


class TestFieldComparison:
    """Tests for FieldComparison model."""

    def test_match_result(self):
        """Test field comparison with match."""
        comp = FieldComparison(
            field_name="first_name",
            visual_value="JOHN",
            mrz_value="JOHN",
            match_result="match",
            similarity_score=1.0,
            match_type="exact",
        )
        assert comp.match_result == "match"

    def test_mismatch_result(self):
        """Test field comparison with mismatch."""
        comp = FieldComparison(
            field_name="first_name",
            visual_value="JOHN",
            mrz_value="JANE",
            match_result="mismatch",
            similarity_score=0.5,
            match_type="fuzzy",
        )
        assert comp.match_result == "mismatch"


class TestCrossValidationResult:
    """Tests for CrossValidationResult model."""

    def test_add_comparison(self):
        """Test adding comparisons."""
        result = CrossValidationResult()

        result.add_comparison(
            FieldComparison(
                field_name="first_name",
                visual_value="JOHN",
                mrz_value="JOHN",
                match_result="match",
                match_type="exact",
            )
        )

        assert result.total_fields == 1
        assert result.matched_fields == 1
        assert result.mismatched_fields == 0

    def test_match_ratio(self):
        """Test match_ratio calculation."""
        result = CrossValidationResult()

        result.add_comparison(
            FieldComparison(
                field_name="first_name",
                match_result="match",
                match_type="exact",
            )
        )
        result.add_comparison(
            FieldComparison(
                field_name="last_name",
                match_result="mismatch",
                match_type="exact",
            )
        )

        assert result.match_ratio == 0.5

    def test_to_field_dict(self):
        """Test to_field_dict conversion."""
        result = CrossValidationResult()

        result.add_comparison(
            FieldComparison(
                field_name="first_name",
                match_result="match",
                match_type="exact",
            )
        )
        result.add_comparison(
            FieldComparison(
                field_name="last_name",
                match_result="mismatch",
                match_type="exact",
            )
        )

        d = result.to_field_dict()
        assert d == {
            "first_name": "match",
            "last_name": "mismatch",
        }


class TestPassportAnalysisResult:
    """Tests for PassportAnalysisResult model."""

    def test_is_valid_true(self):
        """Test is_valid when no errors and score > 0."""
        result = PassportAnalysisResult(
            extracted_passport_data=VisualPassportData(),
            accuracy_score=85,
        )
        assert result.is_valid is True

    def test_is_valid_false_with_errors(self):
        """Test is_valid when errors present."""
        result = PassportAnalysisResult(
            extracted_passport_data=VisualPassportData(),
            accuracy_score=85,
            processing_errors=["Some error"],
        )
        assert result.is_valid is False

    def test_has_mrz(self):
        """Test has_mrz property."""
        result_no_mrz = PassportAnalysisResult(
            extracted_passport_data=VisualPassportData()
        )
        assert result_no_mrz.has_mrz is False

        result_with_mrz = PassportAnalysisResult(
            extracted_passport_data=VisualPassportData(),
            extracted_mrz_data=MRZData(
                document_type="P",
                issuing_country="UTO",
                last_name="DOE",
                first_name="JOHN",
                passport_number="123456789",
                nationality="UTO",
                date_of_birth=date(1990, 1, 1),
                sex="M",
                expiry_date=date(2030, 1, 1),
                raw_line1="X" * 44,
                raw_line2="X" * 44,
            ),
        )
        assert result_with_mrz.has_mrz is True

    def test_to_summary(self):
        """Test to_summary method."""
        result = PassportAnalysisResult(
            extracted_passport_data=VisualPassportData(),
            accuracy_score=85,
            confidence_level="HIGH",
        )

        summary = result.to_summary()
        assert summary["accuracy_score"] == 85
        assert summary["confidence_level"] == "HIGH"
        assert summary["has_mrz"] is False
