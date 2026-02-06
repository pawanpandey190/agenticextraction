"""Unit tests for data models."""

import pytest

from education_agent.config.constants import (
    AcademicLevel,
    DocumentType,
    GradingSystem,
    SemesterValidationStatus,
)
from education_agent.models.credential_data import (
    BachelorValidation,
    CredentialData,
    GradeInfo,
    Institution,
    SemesterRecord,
)
from education_agent.models.evaluation import (
    AnalysisResult,
    DocumentAnalyzed,
    EvaluationResult,
    GradeConversionResult,
    HighestQualification,
    SemesterValidationResult,
)
from education_agent.models.grade_conversion import (
    CountryGradingSystem,
    GradeConversionTable,
    GradeRange,
    LetterGradeMapping,
)


class TestAcademicLevel:
    """Tests for AcademicLevel enum."""

    def test_rank_ordering(self):
        """Test that academic levels have correct ranks."""
        assert AcademicLevel.SECONDARY.rank == 1
        assert AcademicLevel.DIPLOMA.rank == 2
        assert AcademicLevel.BACHELOR.rank == 3
        assert AcademicLevel.MASTER.rank == 4
        assert AcademicLevel.DOCTORATE.rank == 5
        assert AcademicLevel.TRANSCRIPT.rank == 0
        assert AcademicLevel.OTHER.rank == 0

    def test_rank_comparison(self):
        """Test that ranks can be used for comparison."""
        assert AcademicLevel.DOCTORATE.rank > AcademicLevel.MASTER.rank
        assert AcademicLevel.MASTER.rank > AcademicLevel.BACHELOR.rank
        assert AcademicLevel.BACHELOR.rank > AcademicLevel.DIPLOMA.rank


class TestGradeRange:
    """Tests for GradeRange model."""

    def test_contains(self):
        """Test range containment check."""
        grade_range = GradeRange(min_value=60, max_value=80, french_min=12, french_max=16)

        assert grade_range.contains(60)
        assert grade_range.contains(70)
        assert grade_range.contains(80)
        assert not grade_range.contains(59.9)
        assert not grade_range.contains(80.1)

    def test_convert_linear_interpolation(self):
        """Test linear interpolation conversion."""
        grade_range = GradeRange(min_value=0, max_value=100, french_min=0, french_max=20)

        assert grade_range.convert(0) == 0
        assert grade_range.convert(50) == 10
        assert grade_range.convert(100) == 20
        assert grade_range.convert(75) == 15

    def test_convert_non_linear_mapping(self):
        """Test conversion with non-linear mapping."""
        grade_range = GradeRange(min_value=75, max_value=100, french_min=14, french_max=20)

        # At min value
        assert grade_range.convert(75) == 14

        # At max value
        assert grade_range.convert(100) == 20

        # At midpoint
        assert grade_range.convert(87.5) == 17  # (14 + 20) / 2

    def test_convert_single_point_range(self):
        """Test conversion when range is a single point."""
        grade_range = GradeRange(min_value=100, max_value=100, french_min=18, french_max=20)

        assert grade_range.convert(100) == 19  # midpoint


class TestLetterGradeMapping:
    """Tests for LetterGradeMapping model."""

    def test_get_french_equivalent(self):
        """Test getting French equivalent for letter grade."""
        mapping = LetterGradeMapping(letter="A", french_min=16, french_max=20)

        assert mapping.get_french_equivalent() == 18  # midpoint


class TestCountryGradingSystem:
    """Tests for CountryGradingSystem model."""

    def test_convert_numeric(self):
        """Test numeric grade conversion."""
        system = CountryGradingSystem(
            country_code="IN",
            country_name="India",
            system_type="percentage",
            numeric_ranges=[
                GradeRange(min_value=75, max_value=100, french_min=14, french_max=20),
                GradeRange(min_value=60, max_value=74.99, french_min=12, french_max=13.99),
            ],
        )

        # Test within first range
        result = system.convert_numeric(85)
        assert result is not None
        assert 14 <= result <= 20

        # Test within second range
        result = system.convert_numeric(65)
        assert result is not None
        assert 12 <= result <= 14

        # Test outside all ranges
        result = system.convert_numeric(50)
        assert result is None

    def test_convert_letter(self):
        """Test letter grade conversion."""
        system = CountryGradingSystem(
            country_code="US",
            country_name="United States",
            system_type="gpa_4",
            letter_mappings=[
                LetterGradeMapping(letter="A", french_min=16, french_max=20),
                LetterGradeMapping(letter="B", french_min=12, french_max=16),
            ],
        )

        assert system.convert_letter("A") == 18
        assert system.convert_letter("B") == 14  # (12 + 16) / 2 = 14
        assert system.convert_letter("C") is None  # not in mappings


class TestBachelorValidation:
    """Tests for BachelorValidation model."""

    def test_create_complete(self):
        """Test creating validation for complete semesters."""
        validation = BachelorValidation.create(
            expected_semesters=8,
            found_semesters=[1, 2, 3, 4, 5, 6, 7, 8],
        )

        assert validation.is_complete
        assert validation.semesters_missing == []
        assert len(validation.semesters_found) == 8

    def test_create_incomplete(self):
        """Test creating validation for incomplete semesters."""
        validation = BachelorValidation.create(
            expected_semesters=8,
            found_semesters=[1, 2, 3, 5, 6, 8],
        )

        assert not validation.is_complete
        assert validation.semesters_missing == [4, 7]
        assert len(validation.semesters_found) == 6

    def test_create_empty(self):
        """Test creating validation with no semesters found."""
        validation = BachelorValidation.create(
            expected_semesters=6,
            found_semesters=[],
        )

        assert not validation.is_complete
        assert validation.semesters_missing == [1, 2, 3, 4, 5, 6]


class TestCredentialData:
    """Tests for CredentialData model."""

    def test_country_property(self):
        """Test country property."""
        credential = CredentialData(
            source_file="/path/to/file.pdf",
            institution=Institution(name="Test University", country="IN"),
        )

        assert credential.country == "IN"

    def test_country_property_no_institution(self):
        """Test country property when no institution."""
        credential = CredentialData(source_file="/path/to/file.pdf")

        assert credential.country is None

    def test_is_bachelor_property(self):
        """Test is_bachelor property."""
        bachelor = CredentialData(
            source_file="/path/to/file.pdf",
            academic_level=AcademicLevel.BACHELOR,
        )
        master = CredentialData(
            source_file="/path/to/file.pdf",
            academic_level=AcademicLevel.MASTER,
        )

        assert bachelor.is_bachelor
        assert not master.is_bachelor

    def test_is_semester_mark_sheet_property(self):
        """Test is_semester_mark_sheet property."""
        semester_sheet = CredentialData(
            source_file="/path/to/file.pdf",
            document_type=DocumentType.SEMESTER_MARK_SHEET,
        )
        degree = CredentialData(
            source_file="/path/to/file.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
        )

        assert semester_sheet.is_semester_mark_sheet
        assert not degree.is_semester_mark_sheet


class TestGradeInfo:
    """Tests for GradeInfo model."""

    def test_is_converted_true(self):
        """Test is_converted when conversion exists."""
        grade = GradeInfo(
            original_value="75%",
            numeric_value=75.0,
            grading_system=GradingSystem.PERCENTAGE,
            french_scale_equivalent=14.5,
        )

        assert grade.is_converted

    def test_is_converted_false(self):
        """Test is_converted when no conversion."""
        grade = GradeInfo(
            original_value="75%",
            numeric_value=75.0,
            grading_system=GradingSystem.PERCENTAGE,
        )

        assert not grade.is_converted


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_json_serialization(self):
        """Test that AnalysisResult can be serialized to JSON."""
        result = AnalysisResult(
            documents_analyzed=[
                DocumentAnalyzed(
                    file_name="degree.pdf",
                    document_type=DocumentType.DEGREE_CERTIFICATE,
                    country="IN",
                    institution="Test University",
                    qualification="Bachelor of Technology",
                    grading_system=GradingSystem.PERCENTAGE,
                    academic_level=AcademicLevel.BACHELOR,
                    confidence=0.95,
                )
            ],
            highest_qualification=HighestQualification(
                level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
                institution="Test University",
                country="IN",
                status="Completed",
            ),
            evaluation=EvaluationResult(
                bachelor_rules_applied=True,
                semester_validation=SemesterValidationResult(
                    status=SemesterValidationStatus.COMPLETE,
                    expected_semesters=8,
                    found_semesters=[1, 2, 3, 4, 5, 6, 7, 8],
                    missing_semesters=[],
                ),
                grade_conversion=GradeConversionResult(
                    conversion_source="GRADE CONVERSION TABLES BY REGION",
                    original_grade="75%",
                    original_scale=GradingSystem.PERCENTAGE,
                    french_equivalent_0_20="14.5",
                    conversion_notes="Converted using India percentage rules",
                    conversion_possible=True,
                ),
            ),
            flags=[],
            errors=[],
        )

        json_str = result.model_dump_json()
        assert "degree.pdf" in json_str
        assert "BACHELOR" in json_str
        assert "14.5" in json_str
