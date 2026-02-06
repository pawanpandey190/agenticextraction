"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from unittest.mock import Mock
import tempfile
import os

from master_orchestrator.config.settings import Settings
from master_orchestrator.config.constants import ClassificationStrategy, OutputFormat


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
    settings.get_passport_api_key.return_value = "test-key"
    settings.get_financial_api_key.return_value = "test-key"
    settings.get_education_api_key.return_value = "test-key"
    return settings


@pytest.fixture
def temp_folder():
    """Create a temporary folder for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_documents_folder(temp_folder):
    """Create a folder with sample documents for testing."""
    # Create sample PDF-like files
    (temp_folder / "passport_john_doe.pdf").write_bytes(b"%PDF-1.4\nFake passport content")
    (temp_folder / "bank_statement_2024.pdf").write_bytes(b"%PDF-1.4\nFake bank statement")
    (temp_folder / "transcript_semester_1.pdf").write_bytes(b"%PDF-1.4\nFake transcript")
    return temp_folder


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set required environment variables for tests."""
    monkeypatch.setenv("MO_ANTHROPIC_API_KEY", "test-api-key")
