"""Pytest configuration and fixtures."""

import pytest

from passport_agent.config.settings import Settings
from passport_agent.services.mrz_service import MRZService


@pytest.fixture
def mrz_service() -> MRZService:
    """Create MRZ service instance."""
    return MRZService()


@pytest.fixture
def sample_mrz_line1() -> str:
    """Sample MRZ line 1 (ICAO test passport)."""
    return "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"


@pytest.fixture
def sample_mrz_line2() -> str:
    """Sample MRZ line 2 (ICAO test passport).

    Note: The composite check digit (last char) is calculated as 8
    based on ICAO 9303 algorithm for the data in positions 0-9, 13-19, 21-42.
    """
    return "L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08"


@pytest.fixture
def sample_mrz_lines(sample_mrz_line1: str, sample_mrz_line2: str) -> tuple[str, str]:
    """Sample MRZ lines as tuple."""
    return (sample_mrz_line1, sample_mrz_line2)


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing.

    Note: This requires PA_ANTHROPIC_API_KEY to be set,
    even for unit tests that don't use the API.
    """
    import os

    # Set a dummy key for testing if not present
    if "PA_ANTHROPIC_API_KEY" not in os.environ:
        os.environ["PA_ANTHROPIC_API_KEY"] = "test-key-for-unit-tests"

    return Settings()
