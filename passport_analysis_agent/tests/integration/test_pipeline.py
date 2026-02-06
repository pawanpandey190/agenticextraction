"""Integration tests for the passport analysis pipeline.

Note: These tests require a valid API key and sample passport images.
They are marked as integration tests and can be skipped in CI.
"""

import os
from pathlib import Path

import pytest

# Skip all integration tests if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("PA_ANTHROPIC_API_KEY"),
    reason="PA_ANTHROPIC_API_KEY not set",
)


class TestPipelineIntegration:
    """Integration tests for the full pipeline."""

    @pytest.fixture
    def sample_passport_path(self) -> Path | None:
        """Get path to sample passport image if available."""
        # Look for sample files in test data directory
        test_data_dir = Path(__file__).parent.parent / "data"
        if not test_data_dir.exists():
            return None

        # Look for any supported file
        for ext in [".pdf", ".png", ".jpg", ".jpeg"]:
            files = list(test_data_dir.glob(f"*{ext}"))
            if files:
                return files[0]

        return None

    @pytest.mark.integration
    def test_full_pipeline_with_sample(self, sample_passport_path):
        """Test full pipeline with sample passport."""
        if sample_passport_path is None:
            pytest.skip("No sample passport image available")

        from passport_agent.config.settings import get_settings
        from passport_agent.pipeline.orchestrator import PassportPipelineOrchestrator

        settings = get_settings()
        orchestrator = PassportPipelineOrchestrator(settings)

        result = orchestrator.process(str(sample_passport_path))

        # Basic assertions
        assert result is not None
        assert result.extracted_passport_data is not None
        assert 0 <= result.accuracy_score <= 100
        assert result.confidence_level in ["LOW", "MEDIUM", "HIGH"]

    @pytest.mark.integration
    def test_pipeline_error_handling(self):
        """Test pipeline handles missing files gracefully."""
        from passport_agent.config.settings import get_settings
        from passport_agent.pipeline.orchestrator import PassportPipelineOrchestrator
        from passport_agent.utils.exceptions import DocumentLoadError

        settings = get_settings()
        orchestrator = PassportPipelineOrchestrator(settings)

        with pytest.raises(DocumentLoadError):
            orchestrator.process("/nonexistent/file.pdf")


class TestMRZServiceIntegration:
    """Integration tests for MRZ service."""

    def test_parse_icao_test_passport(self):
        """Test parsing ICAO test passport MRZ."""
        from passport_agent.services.mrz_service import MRZService

        service = MRZService()

        line1 = "P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<"
        line2 = "L898902C36UTO7408122F1204159<<<<<<<<<<<<<<08"

        result = service.parse_td3(line1, line2)

        # Verify all fields
        assert result.document_type == "P"
        assert result.issuing_country == "UTO"
        assert result.last_name == "ERIKSSON"
        assert result.first_name == "ANNA MARIA"
        assert result.passport_number == "L898902C3"
        assert result.nationality == "UTO"
        assert str(result.date_of_birth) == "1974-08-12"
        assert result.sex == "F"
        assert str(result.expiry_date) == "2012-04-15"

        # All checksums should be valid
        assert result.checksum_results.all_valid is True
