"""Unit tests for data models."""

import pytest
from pathlib import Path

from master_orchestrator.config.constants import (
    DocumentCategory,
    ValidationStatus,
    WorthinessStatus,
)
from master_orchestrator.models.input import (
    DocumentInfo,
    ClassificationResult,
    DocumentBatch,
)
from master_orchestrator.models.unified_result import (
    PassportDetails,
    EducationSummary,
    FinancialSummary,
    CrossValidation,
    MasterAnalysisResult,
    MRZDetails,
)


class TestDocumentInfo:
    """Tests for DocumentInfo model."""

    def test_is_classified_when_unknown(self):
        """Test is_classified returns False for unknown category."""
        doc = DocumentInfo(
            file_path=Path("/test/doc.pdf"),
            file_name="doc.pdf",
            file_extension=".pdf",
            file_size_bytes=1000,
            category=DocumentCategory.UNKNOWN,
        )
        assert not doc.is_classified

    def test_is_classified_when_known(self):
        """Test is_classified returns True for known category."""
        doc = DocumentInfo(
            file_path=Path("/test/doc.pdf"),
            file_name="doc.pdf",
            file_extension=".pdf",
            file_size_bytes=1000,
            category=DocumentCategory.PASSPORT,
        )
        assert doc.is_classified


class TestDocumentBatch:
    """Tests for DocumentBatch model."""

    def test_total_documents(self):
        """Test total_documents calculation."""
        batch = DocumentBatch()
        batch.passport_documents.append(
            DocumentInfo(
                file_path=Path("/test/passport.pdf"),
                file_name="passport.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            )
        )
        batch.financial_documents.append(
            DocumentInfo(
                file_path=Path("/test/bank.pdf"),
                file_name="bank.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            )
        )
        assert batch.total_documents == 2

    def test_has_all_required_categories_false(self):
        """Test has_all_required_categories when missing categories."""
        batch = DocumentBatch()
        batch.passport_documents.append(
            DocumentInfo(
                file_path=Path("/test/passport.pdf"),
                file_name="passport.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            )
        )
        assert not batch.has_all_required_categories

    def test_has_all_required_categories_true(self):
        """Test has_all_required_categories when all present."""
        batch = DocumentBatch()
        batch.passport_documents.append(
            DocumentInfo(
                file_path=Path("/test/passport.pdf"),
                file_name="passport.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            )
        )
        batch.financial_documents.append(
            DocumentInfo(
                file_path=Path("/test/bank.pdf"),
                file_name="bank.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            )
        )
        batch.education_documents.append(
            DocumentInfo(
                file_path=Path("/test/transcript.pdf"),
                file_name="transcript.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            )
        )
        assert batch.has_all_required_categories

    def test_missing_categories(self):
        """Test missing_categories returns correct list."""
        batch = DocumentBatch()
        batch.passport_documents.append(
            DocumentInfo(
                file_path=Path("/test/passport.pdf"),
                file_name="passport.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            )
        )
        missing = batch.missing_categories
        assert DocumentCategory.FINANCIAL in missing
        assert DocumentCategory.EDUCATION in missing
        assert DocumentCategory.PASSPORT not in missing


class TestPassportDetails:
    """Tests for PassportDetails model."""

    def test_full_name_both_present(self):
        """Test full_name when both names present."""
        details = PassportDetails(first_name="John", last_name="Doe")
        assert details.full_name == "John Doe"

    def test_full_name_only_first(self):
        """Test full_name when only first name present."""
        details = PassportDetails(first_name="John")
        assert details.full_name == "John"

    def test_full_name_only_last(self):
        """Test full_name when only last name present."""
        details = PassportDetails(last_name="Doe")
        assert details.full_name == "Doe"

    def test_full_name_none(self):
        """Test full_name when both names absent."""
        details = PassportDetails()
        assert details.full_name is None


class TestMasterAnalysisResult:
    """Tests for MasterAnalysisResult model."""

    def test_to_output_dict_empty(self):
        """Test to_output_dict with no data."""
        result = MasterAnalysisResult()
        output = result.to_output_dict()
        assert output == {}

    def test_to_output_dict_with_passport(self):
        """Test to_output_dict with passport data."""
        result = MasterAnalysisResult(
            passport_details=PassportDetails(
                first_name="John",
                last_name="Doe",
                date_of_birth="1990-01-15",
                sex="M",
                passport_number="AB123456",
                issuing_country="USA",
                accuracy_score=95,
            )
        )
        output = result.to_output_dict()

        assert "passport_details" in output
        assert output["passport_details"]["first_name"] == "John"
        assert output["passport_details"]["last_name"] == "Doe"
        assert output["passport_details"]["accuracy_score"] == 95

    def test_to_output_dict_with_all_sections(self):
        """Test to_output_dict with all sections."""
        result = MasterAnalysisResult(
            passport_details=PassportDetails(first_name="John", last_name="Doe"),
            education_summary=EducationSummary(
                highest_qualification="Bachelor",
                validation_status=ValidationStatus.PASS,
            ),
            financial_summary=FinancialSummary(
                document_type="BANK_STATEMENT",
                worthiness_status=WorthinessStatus.PASS,
            ),
            cross_validation=CrossValidation(
                name_match=True,
                dob_match=True,
            ),
        )
        output = result.to_output_dict()

        assert "passport_details" in output
        assert "education_summary" in output
        assert "financial_summary" in output
        assert "cross_validation" in output
        assert output["education_summary"]["validation_status"] == "PASS"
        assert output["financial_summary"]["worthiness_status"] == "PASS"
