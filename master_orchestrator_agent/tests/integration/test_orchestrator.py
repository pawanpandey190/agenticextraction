"""Integration tests for MasterOrchestrator."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json

from master_orchestrator.config.settings import Settings
from master_orchestrator.config.constants import OutputFormat, ClassificationStrategy
from master_orchestrator.pipeline.orchestrator import MasterOrchestrator
from master_orchestrator.models.unified_result import MasterAnalysisResult
from master_orchestrator.utils.exceptions import MasterOrchestratorError


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
    settings.output_format = OutputFormat.JSON
    settings.enable_parallel_dispatch = False  # Use sequential for simpler testing
    settings.parallel_dispatch_timeout_seconds = 300
    settings.get_passport_api_key.return_value = "test-key"
    settings.get_financial_api_key.return_value = "test-key"
    settings.get_education_api_key.return_value = "test-key"
    return settings


@pytest.fixture
def test_documents_folder():
    """Create a temporary folder with test documents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test files with appropriate names for filename-based classification
        (Path(tmpdir) / "passport_test.pdf").write_bytes(b"%PDF-1.4 fake passport")
        (Path(tmpdir) / "bank_statement_test.pdf").write_bytes(b"%PDF-1.4 fake bank")
        (Path(tmpdir) / "transcript_test.pdf").write_bytes(b"%PDF-1.4 fake transcript")
        yield Path(tmpdir)


class TestMasterOrchestratorIntegration:
    """Integration tests for MasterOrchestrator."""

    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.PassportAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.FinancialAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.EducationAgentAdapter")
    def test_full_pipeline_with_mocked_agents(
        self,
        mock_education_adapter,
        mock_financial_adapter,
        mock_passport_adapter,
        mock_settings,
        test_documents_folder,
    ):
        """Test full pipeline with mocked sub-agents."""
        # Create mock passport result
        mock_passport_result = Mock()
        mock_passport_result.extracted_passport_data = Mock()
        mock_passport_result.extracted_passport_data.first_name = "John"
        mock_passport_result.extracted_passport_data.last_name = "Doe"
        mock_passport_result.extracted_passport_data.date_of_birth = None
        mock_passport_result.extracted_passport_data.sex = "M"
        mock_passport_result.extracted_passport_data.passport_number = "AB123456"
        mock_passport_result.extracted_passport_data.issuing_country = "USA"
        mock_passport_result.extracted_passport_data.passport_issue_date = None
        mock_passport_result.extracted_passport_data.passport_expiry_date = None
        mock_passport_result.extracted_mrz_data = None
        mock_passport_result.accuracy_score = 85

        # Create mock financial result
        mock_financial_result = Mock()
        mock_financial_result.document_type = Mock()
        mock_financial_result.document_type.value = "BANK_STATEMENT"
        mock_financial_result.account_holder = "John Doe"
        mock_financial_result.bank_name = "Test Bank"
        mock_financial_result.currency_detected = "EUR"
        mock_financial_result.converted_to_eur = Mock()
        mock_financial_result.converted_to_eur.amount_eur = 20000.0
        mock_financial_result.converted_to_eur.original_amount = 20000.0
        mock_financial_result.financial_worthiness = Mock()
        mock_financial_result.financial_worthiness.decision = Mock()
        mock_financial_result.financial_worthiness.decision.value = "WORTHY"
        mock_financial_result.financial_worthiness.threshold_eur = 15000.0
        mock_financial_result.financial_worthiness.reason = "Above threshold"

        # Create mock education result
        mock_education_result = Mock()
        mock_education_result.highest_qualification = Mock()
        mock_education_result.highest_qualification.qualification_name = "Bachelor of Science"
        mock_education_result.highest_qualification.institution = "Test University"
        mock_education_result.highest_qualification.country = "US"
        mock_education_result.evaluation = Mock()
        mock_education_result.evaluation.grade_conversion = Mock()
        mock_education_result.evaluation.grade_conversion.original_grade = "3.5"
        mock_education_result.evaluation.grade_conversion.french_equivalent_0_20 = "14.0"
        mock_education_result.evaluation.grade_conversion.conversion_notes = ""
        mock_education_result.evaluation.semester_validation = Mock()
        mock_education_result.evaluation.semester_validation.status = Mock()
        mock_education_result.evaluation.semester_validation.status.value = "VALID"
        mock_education_result.documents_analyzed = []

        # Setup adapter mocks
        mock_passport_adapter_instance = Mock()
        mock_passport_adapter_instance.process.return_value = mock_passport_result
        mock_passport_adapter.return_value = mock_passport_adapter_instance

        mock_financial_adapter_instance = Mock()
        mock_financial_adapter_instance.process.return_value = mock_financial_result
        mock_financial_adapter.return_value = mock_financial_adapter_instance

        mock_education_adapter_instance = Mock()
        mock_education_adapter_instance.process.return_value = mock_education_result
        mock_education_adapter.return_value = mock_education_adapter_instance

        # Run orchestrator
        with tempfile.TemporaryDirectory() as output_dir:
            orchestrator = MasterOrchestrator(settings=mock_settings)
            result = orchestrator.process(
                input_folder=test_documents_folder,
                output_dir=Path(output_dir),
                output_format=OutputFormat.JSON,
            )

            # Verify result
            assert isinstance(result, MasterAnalysisResult)
            assert result.passport_details is not None
            assert result.passport_details.first_name == "John"
            assert result.passport_details.last_name == "Doe"

            assert result.financial_summary is not None
            assert result.financial_summary.amount_eur == 20000.0

            assert result.education_summary is not None
            assert result.education_summary.highest_qualification == "Bachelor of Science"

            # Verify cross-validation
            assert result.cross_validation is not None
            assert result.cross_validation.name_match is True  # John Doe matches

            # Verify output file was created
            json_file = Path(output_dir) / "analysis_result.json"
            assert json_file.exists()

            with open(json_file) as f:
                output_data = json.load(f)

            assert "passport_details" in output_data
            assert "financial_summary" in output_data
            assert "education_summary" in output_data
            assert "cross_validation" in output_data

    def test_missing_documents_raises_error(self, mock_settings):
        """Test that missing document categories raise appropriate error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Only create passport document
            (Path(tmpdir) / "passport_test.pdf").write_bytes(b"%PDF-1.4 fake")

            orchestrator = MasterOrchestrator(settings=mock_settings)

            with pytest.raises(MasterOrchestratorError) as exc_info:
                orchestrator.process(input_folder=Path(tmpdir))

            assert "Missing required document categories" in str(exc_info.value)
