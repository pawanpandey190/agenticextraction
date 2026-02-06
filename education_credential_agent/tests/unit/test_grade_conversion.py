"""Unit tests for grade conversion functionality."""

import pytest

from education_agent.config.constants import AcademicLevel, DocumentType, GradingSystem
from education_agent.models.credential_data import CredentialData, GradeInfo, Institution
from education_agent.models.grade_conversion import (
    CountryGradingSystem,
    GradeConversionTable,
    GradeRange,
    LetterGradeMapping,
)
from education_agent.pipeline.stages.grade_converter import GradeConverterStage
from education_agent.services.grade_table_service import GradeTableService


class TestGradeConversionTable:
    """Tests for GradeConversionTable."""

    def test_get_country_system(self, sample_grade_table: GradeConversionTable):
        """Test retrieving country-specific grading system."""
        india = sample_grade_table.get_country_system("IN")
        assert india is not None
        assert india.country_name == "India"

        us = sample_grade_table.get_country_system("US")
        assert us is not None
        assert us.country_name == "United States"

        # Non-existent country
        unknown = sample_grade_table.get_country_system("XX")
        assert unknown is None

    def test_get_country_system_case_insensitive(self, sample_grade_table: GradeConversionTable):
        """Test that country lookup is case insensitive."""
        india_upper = sample_grade_table.get_country_system("IN")
        india_lower = sample_grade_table.get_country_system("in")

        assert india_upper is not None
        assert india_lower is not None
        assert india_upper.country_code == india_lower.country_code

    def test_convert_percentage_with_country(self, sample_grade_table: GradeConversionTable):
        """Test percentage conversion with country-specific rules."""
        # India: 75% should be in first range (14-20)
        result = sample_grade_table.convert_percentage(75, "IN")
        assert result is not None
        assert 14 <= result <= 20

        # India: 60% should be in second range (12-13.99)
        result = sample_grade_table.convert_percentage(60, "IN")
        assert result is not None
        assert 12 <= result < 14

    def test_convert_percentage_default(self, sample_grade_table: GradeConversionTable):
        """Test percentage conversion with default rules."""
        # Without country, should use default ranges
        result = sample_grade_table.convert_percentage(95, None)
        assert result is not None
        assert 16 <= result <= 20

    def test_convert_percentage_capped(self, sample_grade_table: GradeConversionTable):
        """Test that percentage is capped at 100."""
        result = sample_grade_table.convert_percentage(120, None)
        assert result is not None
        # Should be converted as 100%, not 120%

    def test_convert_gpa_4(self, sample_grade_table: GradeConversionTable):
        """Test GPA 4.0 conversion."""
        # High GPA
        result = sample_grade_table.convert_gpa_4(3.9, "US")
        assert result is not None
        assert 16 <= result <= 20

        # Mid GPA
        result = sample_grade_table.convert_gpa_4(3.0, "US")
        assert result is not None
        assert 12 <= result < 14

    def test_convert_gpa_10(self, sample_grade_table: GradeConversionTable):
        """Test GPA 10.0 conversion."""
        # Using default ranges (no country-specific for GPA 10)
        result = sample_grade_table.convert_gpa_10(9.5, None)
        assert result is not None
        assert 16 <= result <= 20

        result = sample_grade_table.convert_gpa_10(7.5, None)
        assert result is not None
        assert 12 <= result < 14

    def test_convert_letter(self, sample_grade_table: GradeConversionTable):
        """Test letter grade conversion."""
        # US letter grade
        result = sample_grade_table.convert_letter("A", "US")
        assert result is not None
        assert 16 <= result <= 18

        # UK honors
        result = sample_grade_table.convert_letter("First", "GB")
        assert result is not None
        assert 16 <= result <= 20

        # Unknown letter
        result = sample_grade_table.convert_letter("XYZ", "US")
        assert result is None


class TestGradeTableService:
    """Tests for GradeTableService."""

    def test_load_table_json(self, grade_table_path):
        """Test loading grade table from JSON file."""
        service = GradeTableService(grade_table_path)
        table = service.load_table()

        assert table is not None
        assert table.version == "1.0"
        assert len(table.countries) > 0

    def test_load_table_caching(self, grade_table_path):
        """Test that table is cached after loading."""
        service = GradeTableService(grade_table_path)

        table1 = service.load_table()
        table2 = service.load_table()

        assert table1 is table2  # Same instance

    def test_load_table_no_path(self):
        """Test loading with no path returns empty table."""
        service = GradeTableService(None)
        table = service.load_table()

        assert table is not None
        assert len(table.countries) == 0

    def test_reload_table(self, grade_table_path):
        """Test force reloading table."""
        service = GradeTableService(grade_table_path)

        table1 = service.load_table()
        table2 = service.reload_table()

        # New instance after reload
        assert table1 is not table2

    def test_create_default_table(self):
        """Test creating default conversion table."""
        table = GradeTableService.create_default_table()

        assert table is not None
        assert len(table.countries) > 0

        # Check India is included
        india = table.get_country_system("IN")
        assert india is not None

        # Check US is included
        us = table.get_country_system("US")
        assert us is not None

        # Check UK is included
        uk = table.get_country_system("GB")
        assert uk is not None

        # Check Germany is included
        germany = table.get_country_system("DE")
        assert germany is not None


class TestIndiaGradeConversion:
    """Tests specifically for India grading system conversion."""

    def test_first_class_distinction(self, sample_grade_table: GradeConversionTable):
        """Test conversion of first class with distinction (75%+)."""
        result = sample_grade_table.convert_percentage(85, "IN")
        assert result is not None
        assert 14 <= result <= 20

    def test_first_class(self, sample_grade_table: GradeConversionTable):
        """Test conversion of first class (60-74%)."""
        result = sample_grade_table.convert_percentage(68, "IN")
        assert result is not None
        assert 12 <= result < 14

    def test_second_class(self, sample_grade_table: GradeConversionTable):
        """Test conversion of second class (50-59%)."""
        result = sample_grade_table.convert_percentage(55, "IN")
        assert result is not None
        assert 10 <= result < 12

    def test_pass_class(self, sample_grade_table: GradeConversionTable):
        """Test conversion of pass class (40-49%)."""
        result = sample_grade_table.convert_percentage(45, "IN")
        assert result is not None
        assert 8 <= result < 10


class TestUSGradeConversion:
    """Tests specifically for US grading system conversion."""

    def test_gpa_4_0(self, sample_grade_table: GradeConversionTable):
        """Test conversion of perfect 4.0 GPA."""
        result = sample_grade_table.convert_gpa_4(4.0, "US")
        assert result is not None
        assert 16 <= result <= 20

    def test_gpa_3_5(self, sample_grade_table: GradeConversionTable):
        """Test conversion of 3.5 GPA."""
        result = sample_grade_table.convert_gpa_4(3.5, "US")
        assert result is not None
        assert 14 <= result < 16

    def test_letter_grade_a_plus(self, sample_grade_table: GradeConversionTable):
        """Test conversion of A+ letter grade."""
        result = sample_grade_table.convert_letter("A+", "US")
        assert result is not None
        assert 18 <= result <= 20


class TestUKGradeConversion:
    """Tests specifically for UK grading system conversion."""

    def test_first_class_honours(self, sample_grade_table: GradeConversionTable):
        """Test conversion of First Class Honours."""
        result = sample_grade_table.convert_letter("First", "GB")
        assert result is not None
        assert 16 <= result <= 20

    def test_upper_second(self, sample_grade_table: GradeConversionTable):
        """Test conversion of Upper Second (2:1)."""
        result = sample_grade_table.convert_letter("2:1", "GB")
        assert result is not None
        assert 14 <= result < 16

    def test_lower_second(self, sample_grade_table: GradeConversionTable):
        """Test conversion of Lower Second (2:2)."""
        result = sample_grade_table.convert_letter("2:2", "GB")
        assert result is not None
        assert 12 <= result < 14


class TestGermanGradeConversion:
    """Tests specifically for German grading system conversion."""

    def test_sehr_gut(self, sample_grade_table: GradeConversionTable):
        """Test conversion of 'sehr gut' (1.0-1.5)."""
        germany = sample_grade_table.get_country_system("DE")
        assert germany is not None

        result = germany.convert_numeric(1.3)
        assert result is not None
        assert 16 <= result <= 20

    def test_gut(self, sample_grade_table: GradeConversionTable):
        """Test conversion of 'gut' (1.6-2.5)."""
        germany = sample_grade_table.get_country_system("DE")
        assert germany is not None

        result = germany.convert_numeric(2.0)
        assert result is not None
        assert 14 <= result < 16


class TestEdgeCases:
    """Tests for edge cases in grade conversion."""

    def test_boundary_values(self, sample_grade_table: GradeConversionTable):
        """Test conversion at range boundaries."""
        # At exact boundary
        result = sample_grade_table.convert_percentage(75, "IN")
        assert result is not None
        assert result >= 14

    def test_zero_grade(self, sample_grade_table: GradeConversionTable):
        """Test conversion of zero grade."""
        result = sample_grade_table.convert_percentage(0, "IN")
        assert result is not None
        assert result >= 0

    def test_unknown_country_uses_default(self, sample_grade_table: GradeConversionTable):
        """Test that unknown country falls back to default."""
        result = sample_grade_table.convert_percentage(85, "ZZ")
        assert result is not None
        # Should use default percentage ranges


class TestHighestQualificationConversion:
    """Tests for highest qualification only grade conversion."""

    def test_converts_only_highest_qualification(self):
        """Test that only highest credential gets French conversion."""
        from education_agent.config.settings import Settings
        from education_agent.pipeline.base import PipelineContext

        settings = Settings()
        stage = GradeConverterStage(settings)

        # Create credentials: Bachelor's and Master's
        bachelor_cred = CredentialData(
            source_file="/path/to/bachelor.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.BACHELOR,
            qualification_name="Bachelor of Technology",
            institution=Institution(name="Test University", country="IN"),
            final_grade=GradeInfo(
                original_value="75%",
                numeric_value=75.0,
                grading_system=GradingSystem.PERCENTAGE,
            ),
        )

        master_cred = CredentialData(
            source_file="/path/to/master.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.MASTER,
            qualification_name="Master of Technology",
            institution=Institution(name="Test University", country="IN"),
            final_grade=GradeInfo(
                original_value="80%",
                numeric_value=80.0,
                grading_system=GradingSystem.PERCENTAGE,
            ),
        )

        context = PipelineContext()
        context.credentials = [bachelor_cred, master_cred]

        # Process
        result = stage.process(context)

        # Only Master's grade should be converted (highest qualification)
        assert master_cred.final_grade.french_scale_equivalent is not None
        assert bachelor_cred.final_grade.french_scale_equivalent is None

    def test_master_converted_over_bachelor(self):
        """Test that Master's grade is converted when both present."""
        from education_agent.config.settings import Settings
        from education_agent.pipeline.base import PipelineContext

        settings = Settings()
        stage = GradeConverterStage(settings)

        # Create credentials with Master's having lower rank in list
        bachelor_cred = CredentialData(
            source_file="/path/to/bachelor.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.BACHELOR,
            qualification_name="Bachelor of Science",
            institution=Institution(name="MIT", country="US"),
            final_grade=GradeInfo(
                original_value="3.5",
                numeric_value=3.5,
                grading_system=GradingSystem.GPA_4,
            ),
        )

        master_cred = CredentialData(
            source_file="/path/to/master.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.MASTER,
            qualification_name="Master of Science",
            institution=Institution(name="MIT", country="US"),
            final_grade=GradeInfo(
                original_value="3.8",
                numeric_value=3.8,
                grading_system=GradingSystem.GPA_4,
            ),
        )

        context = PipelineContext()
        # Put Bachelor first to ensure Master is still selected
        context.credentials = [bachelor_cred, master_cred]

        result = stage.process(context)

        # Verify Master's grade was converted
        assert master_cred.final_grade.french_scale_equivalent is not None
        # Verify Bachelor's grade was NOT converted
        assert bachelor_cred.final_grade.french_scale_equivalent is None

        # Verify stage result indicates Master was converted
        stage_result = context.get_stage_result("grade_converter")
        assert stage_result["credential_converted"] == "/path/to/master.pdf"

    def test_doctorate_converted_over_master_and_bachelor(self):
        """Test that Doctorate is converted when all levels present."""
        from education_agent.config.settings import Settings
        from education_agent.pipeline.base import PipelineContext

        settings = Settings()
        stage = GradeConverterStage(settings)

        bachelor_cred = CredentialData(
            source_file="/path/to/bachelor.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.BACHELOR,
            final_grade=GradeInfo(
                original_value="70%",
                numeric_value=70.0,
                grading_system=GradingSystem.PERCENTAGE,
            ),
        )

        master_cred = CredentialData(
            source_file="/path/to/master.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.MASTER,
            final_grade=GradeInfo(
                original_value="75%",
                numeric_value=75.0,
                grading_system=GradingSystem.PERCENTAGE,
            ),
        )

        doctorate_cred = CredentialData(
            source_file="/path/to/phd.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.DOCTORATE,
            final_grade=GradeInfo(
                original_value="85%",
                numeric_value=85.0,
                grading_system=GradingSystem.PERCENTAGE,
            ),
        )

        context = PipelineContext()
        context.credentials = [bachelor_cred, master_cred, doctorate_cred]

        result = stage.process(context)

        # Only Doctorate should be converted
        assert doctorate_cred.final_grade.french_scale_equivalent is not None
        assert master_cred.final_grade.french_scale_equivalent is None
        assert bachelor_cred.final_grade.french_scale_equivalent is None

    def test_single_bachelor_still_converted(self):
        """Test that single Bachelor's credential still gets converted."""
        from education_agent.config.settings import Settings
        from education_agent.pipeline.base import PipelineContext

        settings = Settings()
        stage = GradeConverterStage(settings)

        bachelor_cred = CredentialData(
            source_file="/path/to/bachelor.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.BACHELOR,
            qualification_name="Bachelor of Technology",
            institution=Institution(name="Test University", country="IN"),
            final_grade=GradeInfo(
                original_value="75%",
                numeric_value=75.0,
                grading_system=GradingSystem.PERCENTAGE,
            ),
        )

        context = PipelineContext()
        context.credentials = [bachelor_cred]

        result = stage.process(context)

        # Bachelor's grade should be converted when it's the only/highest
        assert bachelor_cred.final_grade.french_scale_equivalent is not None

    def test_mark_sheets_not_considered_for_conversion(self):
        """Test that mark sheets are not considered for grade conversion."""
        from education_agent.config.settings import Settings
        from education_agent.pipeline.base import PipelineContext

        settings = Settings()
        stage = GradeConverterStage(settings)

        # Only semester mark sheets, no degree certificate
        mark_sheet = CredentialData(
            source_file="/path/to/sem1.pdf",
            document_type=DocumentType.SEMESTER_MARK_SHEET,
            academic_level=AcademicLevel.BACHELOR,
            semester_number=1,
            final_grade=GradeInfo(
                original_value="80%",
                numeric_value=80.0,
                grading_system=GradingSystem.PERCENTAGE,
            ),
        )

        context = PipelineContext()
        context.credentials = [mark_sheet]

        result = stage.process(context)

        # Mark sheet should NOT be converted
        assert mark_sheet.final_grade.french_scale_equivalent is None

        # Stage should indicate no degree credential found
        stage_result = context.get_stage_result("grade_converter")
        assert stage_result["conversions_successful"] == 0
