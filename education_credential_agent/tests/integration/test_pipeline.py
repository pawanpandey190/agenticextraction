"""Integration tests for the pipeline."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from education_agent.config.constants import AcademicLevel, DocumentType, GradingSystem
from education_agent.models.credential_data import CredentialData, GradeInfo, Institution
from education_agent.models.evaluation import AnalysisResult
from education_agent.pipeline.base import PipelineContext
from education_agent.services.grade_table_service import GradeTableService


class TestPipelineContext:
    """Tests for PipelineContext functionality."""

    def test_add_and_get_extracted_text(self):
        """Test adding and retrieving extracted text."""
        context = PipelineContext()

        context.add_extracted_text("/path/to/doc1.pdf", "Extracted text 1")
        context.add_extracted_text("/path/to/doc2.pdf", "Extracted text 2")

        assert context.get_extracted_text("/path/to/doc1.pdf") == "Extracted text 1"
        assert context.get_extracted_text("/path/to/doc2.pdf") == "Extracted text 2"
        assert context.get_extracted_text("/path/to/doc3.pdf") is None

    def test_add_and_get_first_page_image(self):
        """Test adding and retrieving first page images."""
        context = PipelineContext()

        context.add_first_page_image("/path/to/doc.pdf", "base64data", "image/png")

        result = context.get_first_page_image("/path/to/doc.pdf")
        assert result is not None
        assert result == ("base64data", "image/png")

        assert context.get_first_page_image("/path/to/other.pdf") is None

    def test_add_and_get_credential(self):
        """Test adding and retrieving credentials."""
        context = PipelineContext()

        credential = CredentialData(
            source_file="/path/to/degree.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.BACHELOR,
        )

        context.add_credential(credential)

        assert len(context.credentials) == 1
        assert context.get_credential_by_file("/path/to/degree.pdf") == credential
        assert context.get_credential_by_file("/path/to/other.pdf") is None

    def test_set_and_get_stage_result(self):
        """Test stage result storage."""
        context = PipelineContext()

        context.set_stage_result("test_stage", {"key": "value"})

        assert context.get_stage_result("test_stage") == {"key": "value"}
        assert context.get_stage_result("other_stage") is None


class TestGradeTableServiceIntegration:
    """Integration tests for grade table service."""

    def test_load_and_convert(self, grade_table_path):
        """Test loading table and converting grades."""
        service = GradeTableService(grade_table_path)
        table = service.load_table()

        # Convert Indian percentage
        result = table.convert_percentage(80, "IN")
        assert result is not None
        assert 14 <= result <= 20

    def test_create_default_and_convert(self):
        """Test creating default table and converting grades."""
        table = GradeTableService.create_default_table()

        # India percentage
        india_result = table.convert_percentage(75, "IN")
        assert india_result is not None
        assert india_result >= 14

        # US GPA
        us_result = table.convert_gpa_4(3.8, "US")
        assert us_result is not None
        assert us_result >= 16

        # UK honors
        uk_result = table.convert_letter("First", "GB")
        assert uk_result is not None
        assert uk_result >= 16


class TestAnalysisResultSerialization:
    """Tests for analysis result JSON serialization."""

    def test_complete_result_serialization(self):
        """Test serializing a complete analysis result."""
        from education_agent.models.evaluation import (
            DocumentAnalyzed,
            EvaluationResult,
            GradeConversionResult,
            HighestQualification,
            SemesterValidationResult,
        )
        from education_agent.config.constants import SemesterValidationStatus

        result = AnalysisResult(
            documents_analyzed=[
                DocumentAnalyzed(
                    file_name="degree.pdf",
                    document_type=DocumentType.DEGREE_CERTIFICATE,
                    country="IN",
                    institution="IIT Delhi",
                    qualification="Bachelor of Technology",
                    grading_system=GradingSystem.PERCENTAGE,
                    academic_level=AcademicLevel.BACHELOR,
                    confidence=0.95,
                ),
                DocumentAnalyzed(
                    file_name="sem1.pdf",
                    document_type=DocumentType.SEMESTER_MARK_SHEET,
                    country="IN",
                    institution="IIT Delhi",
                    academic_level=AcademicLevel.BACHELOR,
                    semester_number=1,
                    confidence=0.9,
                ),
            ],
            highest_qualification=HighestQualification(
                level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
                institution="IIT Delhi",
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
            processing_summary={
                "total_documents": 9,
                "credentials_extracted": 9,
                "pages_processed": 15,
                "duration_seconds": 45.5,
            },
        )

        # Serialize to JSON
        json_str = result.model_dump_json(indent=2)
        parsed = json.loads(json_str)

        # Verify structure
        assert "documents_analyzed" in parsed
        assert len(parsed["documents_analyzed"]) == 2
        assert parsed["documents_analyzed"][0]["file_name"] == "degree.pdf"

        assert "highest_qualification" in parsed
        assert parsed["highest_qualification"]["level"] == "BACHELOR"

        assert "evaluation" in parsed
        assert parsed["evaluation"]["bachelor_rules_applied"] is True
        assert parsed["evaluation"]["semester_validation"]["status"] == "COMPLETE"
        assert parsed["evaluation"]["grade_conversion"]["french_equivalent_0_20"] == "14.5"

    def test_incomplete_semester_result(self):
        """Test result with incomplete semesters."""
        from education_agent.models.evaluation import (
            DocumentAnalyzed,
            EvaluationResult,
            GradeConversionResult,
            HighestQualification,
            SemesterValidationResult,
        )
        from education_agent.config.constants import SemesterValidationStatus

        result = AnalysisResult(
            documents_analyzed=[
                DocumentAnalyzed(
                    file_name="degree.pdf",
                    document_type=DocumentType.DEGREE_CERTIFICATE,
                    academic_level=AcademicLevel.BACHELOR,
                    confidence=0.9,
                ),
            ],
            highest_qualification=HighestQualification(
                level=AcademicLevel.BACHELOR,
                qualification_name="Bachelor of Technology",
                status="Completed",
            ),
            evaluation=EvaluationResult(
                bachelor_rules_applied=True,
                semester_validation=SemesterValidationResult(
                    status=SemesterValidationStatus.INCOMPLETE,
                    expected_semesters=8,
                    found_semesters=[1, 2, 3, 6, 7, 8],
                    missing_semesters=[4, 5],
                ),
                grade_conversion=GradeConversionResult(
                    conversion_source="GRADE CONVERSION TABLES BY REGION",
                    original_grade="75%",
                    original_scale=GradingSystem.PERCENTAGE,
                    french_equivalent_0_20=None,
                    conversion_notes="Grade not computed - incomplete semester records",
                    conversion_possible=False,
                ),
            ),
            flags=["INCOMPLETE_SEMESTERS: Missing semesters [4, 5]"],
        )

        json_str = result.model_dump_json(indent=2)
        parsed = json.loads(json_str)

        assert parsed["evaluation"]["semester_validation"]["status"] == "INCOMPLETE"
        assert parsed["evaluation"]["semester_validation"]["missing_semesters"] == [4, 5]
        assert parsed["evaluation"]["grade_conversion"]["french_equivalent_0_20"] is None
        assert "INCOMPLETE_SEMESTERS" in parsed["flags"][0]


class TestEndToEndScenarios:
    """End-to-end scenario tests (mocked)."""

    def test_scenario_complete_bachelor_india(self, sample_india_credential, sample_grade_table):
        """Test complete Indian Bachelor's degree evaluation."""
        # This would normally go through the full pipeline
        # Here we test the expected output format

        credential = sample_india_credential

        # Simulate grade conversion
        french_grade = sample_grade_table.convert_percentage(
            credential.final_grade.numeric_value,
            credential.country,
        )

        assert french_grade is not None
        assert 14 <= french_grade <= 20  # 75% should map to ~14-17

    def test_scenario_unknown_country(self, sample_grade_table):
        """Test evaluation with unknown country falls back to defaults."""
        credential = CredentialData(
            source_file="/path/to/degree.pdf",
            document_type=DocumentType.DEGREE_CERTIFICATE,
            academic_level=AcademicLevel.BACHELOR,
            institution=Institution(
                name="Unknown University",
                country="ZZ",  # Invalid country
            ),
            final_grade=GradeInfo(
                original_value="85%",
                numeric_value=85.0,
                grading_system=GradingSystem.PERCENTAGE,
            ),
        )

        # Should still convert using default ranges
        french_grade = sample_grade_table.convert_percentage(85.0, "ZZ")
        assert french_grade is not None

    def test_scenario_non_bachelor_skips_semester_validation(self):
        """Test that non-Bachelor degrees skip semester validation."""
        from education_agent.pipeline.stages.semester_validator import validate_bachelor_semesters

        credentials = [
            CredentialData(
                source_file="/path/to/master.pdf",
                document_type=DocumentType.DEGREE_CERTIFICATE,
                academic_level=AcademicLevel.MASTER,
                qualification_name="Master of Technology",
            )
        ]

        validation = validate_bachelor_semesters(credentials)

        # Should report no Bachelor's found
        assert validation.notes == "No Bachelor's degree found"

    def test_scenario_provisional_certificate(self):
        """Test handling of provisional certificate."""
        credential = CredentialData(
            source_file="/path/to/provisional.pdf",
            document_type=DocumentType.PROVISIONAL_CERTIFICATE,
            academic_level=AcademicLevel.BACHELOR,
            qualification_name="Bachelor of Technology",
            is_provisional=True,
        )

        assert credential.is_provisional
        assert credential.document_type == DocumentType.PROVISIONAL_CERTIFICATE
