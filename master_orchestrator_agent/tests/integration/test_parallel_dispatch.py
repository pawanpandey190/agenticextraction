"""Integration tests for parallel agent dispatch."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import TimeoutError as FuturesTimeoutError

import pytest

from master_orchestrator.config.constants import ClassificationStrategy, OutputFormat
from master_orchestrator.config.settings import Settings
from master_orchestrator.pipeline.stages.agent_dispatcher import AgentDispatcherStage
from master_orchestrator.pipeline.base import MasterPipelineContext
from master_orchestrator.models.input import DocumentBatch, DocumentInfo


@pytest.fixture
def mock_settings_parallel():
    """Create mock settings with parallel dispatch enabled."""
    settings = Mock(spec=Settings)
    settings.anthropic_api_key = "test-key"
    settings.model_name = "claude-sonnet-4-20250514"
    settings.classification_strategy = ClassificationStrategy.FILENAME_ONLY
    settings.name_match_threshold = 0.85
    settings.financial_threshold_eur = 15000.0
    settings.max_file_size_bytes = 52428800
    settings.output_format = OutputFormat.JSON
    settings.enable_parallel_dispatch = True
    settings.parallel_dispatch_timeout_seconds = 30
    settings.get_passport_api_key.return_value = "test-key"
    settings.get_financial_api_key.return_value = "test-key"
    settings.get_education_api_key.return_value = "test-key"
    return settings


@pytest.fixture
def mock_settings_sequential():
    """Create mock settings with parallel dispatch disabled."""
    settings = Mock(spec=Settings)
    settings.anthropic_api_key = "test-key"
    settings.model_name = "claude-sonnet-4-20250514"
    settings.classification_strategy = ClassificationStrategy.FILENAME_ONLY
    settings.name_match_threshold = 0.85
    settings.financial_threshold_eur = 15000.0
    settings.max_file_size_bytes = 52428800
    settings.output_format = OutputFormat.JSON
    settings.enable_parallel_dispatch = False
    settings.parallel_dispatch_timeout_seconds = 30
    settings.get_passport_api_key.return_value = "test-key"
    settings.get_financial_api_key.return_value = "test-key"
    settings.get_education_api_key.return_value = "test-key"
    return settings


@pytest.fixture
def create_mock_context():
    """Factory for creating mock pipeline context."""

    def _create(settings):
        context = MasterPipelineContext(
            input_folder=Path("/fake/input"),
            settings=settings,
        )

        # Create mock document batch
        passport_doc = Mock(spec=DocumentInfo)
        passport_doc.file_path = Path("/fake/passport.pdf")
        passport_doc.file_name = "passport.pdf"

        financial_doc = Mock(spec=DocumentInfo)
        financial_doc.file_path = Path("/fake/bank_statement.pdf")
        financial_doc.file_name = "bank_statement.pdf"

        education_doc = Mock(spec=DocumentInfo)
        education_doc.file_path = Path("/fake/transcript.pdf")
        education_doc.file_name = "transcript.pdf"

        batch = Mock(spec=DocumentBatch)
        batch.passport_documents = [passport_doc]
        batch.financial_documents = [financial_doc]
        batch.education_documents = [education_doc]

        context.document_batch = batch
        return context

    return _create


class TestParallelDispatch:
    """Tests for parallel agent dispatch functionality."""

    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.PassportAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.FinancialAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.EducationAgentAdapter")
    def test_parallel_dispatch_enabled(
        self,
        mock_education_adapter,
        mock_financial_adapter,
        mock_passport_adapter,
        mock_settings_parallel,
        create_mock_context,
    ):
        """Test that parallel dispatch processes all agents concurrently."""
        # Track call order with timestamps
        call_times = {}

        def make_process_fn(name, delay=0.1):
            def process_fn(*args, **kwargs):
                call_times[name] = {"start": time.time()}
                time.sleep(delay)
                call_times[name]["end"] = time.time()
                return Mock()
            return process_fn

        mock_passport_instance = Mock()
        mock_passport_instance.process = make_process_fn("passport", 0.1)
        mock_passport_adapter.return_value = mock_passport_instance

        mock_financial_instance = Mock()
        mock_financial_instance.process = make_process_fn("financial", 0.1)
        mock_financial_adapter.return_value = mock_financial_instance

        mock_education_instance = Mock()
        mock_education_instance.process = make_process_fn("education", 0.1)
        mock_education_adapter.return_value = mock_education_instance

        context = create_mock_context(mock_settings_parallel)
        stage = AgentDispatcherStage()

        start_time = time.time()
        stage.process(context)
        total_time = time.time() - start_time

        # In parallel, total time should be close to the longest single task
        # (not the sum of all tasks)
        # With 3 tasks of 0.1s each, sequential would be ~0.3s, parallel ~0.1s
        # Allow some overhead
        assert total_time < 0.25, f"Parallel dispatch took too long: {total_time}s"

        # Verify all agents were called
        assert context.passport_raw_result is not None
        assert context.financial_raw_result is not None
        assert context.education_raw_result is not None

    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.PassportAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.FinancialAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.EducationAgentAdapter")
    def test_sequential_dispatch(
        self,
        mock_education_adapter,
        mock_financial_adapter,
        mock_passport_adapter,
        mock_settings_sequential,
        create_mock_context,
    ):
        """Test that sequential dispatch processes agents one at a time."""
        call_order = []

        def make_process_fn(name):
            def process_fn(*args, **kwargs):
                call_order.append(name)
                return Mock()
            return process_fn

        mock_passport_instance = Mock()
        mock_passport_instance.process = make_process_fn("passport")
        mock_passport_adapter.return_value = mock_passport_instance

        mock_financial_instance = Mock()
        mock_financial_instance.process = make_process_fn("financial")
        mock_financial_adapter.return_value = mock_financial_instance

        mock_education_instance = Mock()
        mock_education_instance.process = make_process_fn("education")
        mock_education_adapter.return_value = mock_education_instance

        context = create_mock_context(mock_settings_sequential)
        stage = AgentDispatcherStage()

        stage.process(context)

        # Sequential processing should maintain order
        assert call_order == ["passport", "financial", "education"]

    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.PassportAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.FinancialAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.EducationAgentAdapter")
    def test_parallel_partial_failure(
        self,
        mock_education_adapter,
        mock_financial_adapter,
        mock_passport_adapter,
        mock_settings_parallel,
        create_mock_context,
    ):
        """Test that one agent failure doesn't block others in parallel mode."""
        mock_passport_instance = Mock()
        mock_passport_instance.process.return_value = Mock()
        mock_passport_adapter.return_value = mock_passport_instance

        mock_financial_instance = Mock()
        mock_financial_instance.process.side_effect = Exception("Financial agent error")
        mock_financial_adapter.return_value = mock_financial_instance

        mock_education_instance = Mock()
        mock_education_instance.process.return_value = Mock()
        mock_education_adapter.return_value = mock_education_instance

        context = create_mock_context(mock_settings_parallel)
        stage = AgentDispatcherStage()

        # Should not raise exception
        stage.process(context)

        # Passport and education should succeed
        assert context.passport_raw_result is not None
        assert context.education_raw_result is not None

        # Financial should be None due to error
        assert context.financial_raw_result is None

        # Error should be recorded
        assert any("Financial" in err for err in context.errors)

    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.PassportAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.FinancialAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.EducationAgentAdapter")
    def test_parallel_timeout_handling(
        self,
        mock_education_adapter,
        mock_financial_adapter,
        mock_passport_adapter,
        create_mock_context,
    ):
        """Test that timeout is handled properly in parallel mode."""
        # Create settings with very short timeout
        settings = Mock(spec=Settings)
        settings.anthropic_api_key = "test-key"
        settings.enable_parallel_dispatch = True
        settings.parallel_dispatch_timeout_seconds = 1  # Very short timeout
        settings.financial_threshold_eur = 15000.0
        settings.get_passport_api_key.return_value = "test-key"
        settings.get_financial_api_key.return_value = "test-key"
        settings.get_education_api_key.return_value = "test-key"

        # Passport completes quickly
        mock_passport_instance = Mock()
        mock_passport_instance.process.return_value = Mock()
        mock_passport_adapter.return_value = mock_passport_instance

        # Financial takes too long
        def slow_process(*args, **kwargs):
            time.sleep(3)  # Longer than timeout
            return Mock()

        mock_financial_instance = Mock()
        mock_financial_instance.process = slow_process
        mock_financial_adapter.return_value = mock_financial_instance

        # Education completes quickly
        mock_education_instance = Mock()
        mock_education_instance.process.return_value = Mock()
        mock_education_adapter.return_value = mock_education_instance

        context = create_mock_context(settings)
        stage = AgentDispatcherStage()

        # Should complete (with timeout error recorded)
        stage.process(context)

        # Timeout error should be recorded
        # Note: Python ThreadPoolExecutor cannot forcibly stop running threads,
        # so the total time may exceed the timeout. What matters is that the
        # timeout was detected and an error was recorded.
        assert any("timed out" in err.lower() for err in context.errors)

        # Financial result should be None since it timed out
        assert context.financial_raw_result is None

        # Other agents should have completed successfully
        assert context.passport_raw_result is not None
        assert context.education_raw_result is not None

    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.PassportAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.FinancialAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.EducationAgentAdapter")
    def test_parallel_no_documents(
        self,
        mock_education_adapter,
        mock_financial_adapter,
        mock_passport_adapter,
        mock_settings_parallel,
    ):
        """Test parallel dispatch with no documents to process."""
        context = MasterPipelineContext(
            input_folder=Path("/fake/input"),
            settings=mock_settings_parallel,
        )

        # Empty document batch
        batch = Mock(spec=DocumentBatch)
        batch.passport_documents = []
        batch.financial_documents = []
        batch.education_documents = []
        context.document_batch = batch

        # Setup adapter instances
        mock_passport_instance = Mock()
        mock_passport_adapter.return_value = mock_passport_instance
        mock_financial_instance = Mock()
        mock_financial_adapter.return_value = mock_financial_instance
        mock_education_instance = Mock()
        mock_education_adapter.return_value = mock_education_instance

        stage = AgentDispatcherStage()
        stage.process(context)

        # No adapter process methods should be called
        mock_passport_instance.process.assert_not_called()
        mock_financial_instance.process.assert_not_called()
        mock_education_instance.process.assert_not_called()

        # Results should all be None
        assert context.passport_raw_result is None
        assert context.financial_raw_result is None
        assert context.education_raw_result is None

    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.PassportAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.FinancialAgentAdapter")
    @patch("master_orchestrator.pipeline.stages.agent_dispatcher.EducationAgentAdapter")
    def test_parallel_single_document_type(
        self,
        mock_education_adapter,
        mock_financial_adapter,
        mock_passport_adapter,
        mock_settings_parallel,
    ):
        """Test parallel dispatch with only one document type."""
        context = MasterPipelineContext(
            input_folder=Path("/fake/input"),
            settings=mock_settings_parallel,
        )

        # Only passport document
        passport_doc = Mock(spec=DocumentInfo)
        passport_doc.file_path = Path("/fake/passport.pdf")
        passport_doc.file_name = "passport.pdf"

        batch = Mock(spec=DocumentBatch)
        batch.passport_documents = [passport_doc]
        batch.financial_documents = []
        batch.education_documents = []
        context.document_batch = batch

        mock_passport_instance = Mock()
        mock_passport_instance.process.return_value = Mock()
        mock_passport_adapter.return_value = mock_passport_instance

        stage = AgentDispatcherStage()
        stage.process(context)

        # Only passport should be processed
        assert context.passport_raw_result is not None
        assert context.financial_raw_result is None
        assert context.education_raw_result is None
