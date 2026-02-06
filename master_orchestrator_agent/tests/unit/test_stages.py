"""Unit tests for pipeline stages."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from master_orchestrator.config.settings import Settings
from master_orchestrator.config.constants import (
    DocumentCategory,
    ClassificationStrategy,
)
from master_orchestrator.models.input import DocumentInfo, DocumentBatch
from master_orchestrator.models.unified_result import (
    PassportDetails,
    EducationSummary,
    FinancialSummary,
    CrossValidation,
)
from master_orchestrator.pipeline.base import MasterPipelineContext
from master_orchestrator.pipeline.stages.document_scanner import DocumentScannerStage
from master_orchestrator.pipeline.stages.document_classifier import DocumentClassifierStage
from master_orchestrator.pipeline.stages.cross_validator import CrossValidatorStage
from master_orchestrator.utils.exceptions import DocumentScanError, MissingDocumentCategoryError


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.anthropic_api_key = "test-key"
    settings.model_name = "claude-sonnet-4-20250514"
    settings.classification_strategy = ClassificationStrategy.FILENAME_ONLY
    settings.name_match_threshold = 0.85
    settings.financial_threshold_eur = 15000.0
    settings.max_file_size_bytes = 52428800
    return settings


class TestDocumentScannerStage:
    """Tests for DocumentScannerStage."""

    def test_scan_empty_folder(self, mock_settings):
        """Test scanning empty folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            context = MasterPipelineContext(
                input_folder=Path(tmpdir),
                settings=mock_settings,
            )
            stage = DocumentScannerStage()

            with pytest.raises(DocumentScanError) as exc_info:
                stage.process(context)

            assert "No supported documents found" in str(exc_info.value)

    def test_scan_nonexistent_folder(self, mock_settings):
        """Test scanning nonexistent folder."""
        context = MasterPipelineContext(
            input_folder=Path("/nonexistent/folder"),
            settings=mock_settings,
        )
        stage = DocumentScannerStage()

        with pytest.raises(DocumentScanError) as exc_info:
            stage.process(context)

        assert "does not exist" in str(exc_info.value)

    def test_scan_folder_with_documents(self, mock_settings):
        """Test scanning folder with supported documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "passport.pdf").write_text("fake pdf")
            (Path(tmpdir) / "bank.pdf").write_text("fake pdf")
            (Path(tmpdir) / "transcript.png").write_text("fake png")
            (Path(tmpdir) / "readme.txt").write_text("not a document")

            context = MasterPipelineContext(
                input_folder=Path(tmpdir),
                settings=mock_settings,
            )
            stage = DocumentScannerStage()
            result = stage.process(context)

            assert len(result.scanned_documents) == 3
            extensions = {d.file_extension for d in result.scanned_documents}
            assert ".pdf" in extensions
            assert ".png" in extensions
            assert ".txt" not in extensions


class TestDocumentClassifierStage:
    """Tests for DocumentClassifierStage."""

    def test_classify_by_filename_passport(self, mock_settings):
        """Test filename-based classification for passport."""
        context = MasterPipelineContext(
            input_folder=Path("/test"),
            settings=mock_settings,
        )
        context.scanned_documents = [
            DocumentInfo(
                file_path=Path("/test/passport_john.pdf"),
                file_name="passport_john.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            ),
            DocumentInfo(
                file_path=Path("/test/bank_statement.pdf"),
                file_name="bank_statement.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            ),
            DocumentInfo(
                file_path=Path("/test/transcript.pdf"),
                file_name="transcript.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            ),
        ]

        stage = DocumentClassifierStage()
        result = stage.process(context)

        assert result.document_batch is not None
        assert len(result.document_batch.passport_documents) == 1
        assert len(result.document_batch.financial_documents) == 1
        assert len(result.document_batch.education_documents) == 1

    def test_classify_missing_category_raises_error(self, mock_settings):
        """Test that missing categories raise error."""
        context = MasterPipelineContext(
            input_folder=Path("/test"),
            settings=mock_settings,
        )
        context.scanned_documents = [
            DocumentInfo(
                file_path=Path("/test/passport.pdf"),
                file_name="passport.pdf",
                file_extension=".pdf",
                file_size_bytes=1000,
            ),
        ]

        stage = DocumentClassifierStage()

        with pytest.raises(MissingDocumentCategoryError) as exc_info:
            stage.process(context)

        assert "financial" in str(exc_info.value).lower()
        assert "education" in str(exc_info.value).lower()


class TestCrossValidatorStage:
    """Tests for CrossValidatorStage."""

    def test_cross_validate_matching_names(self, mock_settings):
        """Test cross-validation with matching names."""
        context = MasterPipelineContext(
            input_folder=Path("/test"),
            settings=mock_settings,
        )
        context.passport_details = PassportDetails(
            first_name="John",
            last_name="Doe",
            date_of_birth="1990-01-15",
        )
        context.financial_summary = FinancialSummary(
            account_holder_name="John Doe",
        )
        context.education_summary = EducationSummary(
            student_name="John Doe",
        )

        stage = CrossValidatorStage()
        result = stage.process(context)

        assert result.cross_validation is not None
        assert result.cross_validation.name_match is True
        assert result.cross_validation.name_match_score is not None
        assert result.cross_validation.name_match_score >= 0.85

    def test_cross_validate_mismatching_names(self, mock_settings):
        """Test cross-validation with mismatching names."""
        context = MasterPipelineContext(
            input_folder=Path("/test"),
            settings=mock_settings,
        )
        context.passport_details = PassportDetails(
            first_name="John",
            last_name="Doe",
        )
        context.financial_summary = FinancialSummary(
            account_holder_name="Jane Smith",
        )

        stage = CrossValidatorStage()
        result = stage.process(context)

        assert result.cross_validation is not None
        assert result.cross_validation.name_match is False

    def test_cross_validate_no_names_available(self, mock_settings):
        """Test cross-validation when no names available."""
        context = MasterPipelineContext(
            input_folder=Path("/test"),
            settings=mock_settings,
        )
        context.passport_details = PassportDetails()
        context.financial_summary = FinancialSummary()
        context.education_summary = EducationSummary()

        stage = CrossValidatorStage()
        result = stage.process(context)

        assert result.cross_validation is not None
        assert result.cross_validation.name_match is None
        assert "Unable to validate names" in result.cross_validation.remarks
