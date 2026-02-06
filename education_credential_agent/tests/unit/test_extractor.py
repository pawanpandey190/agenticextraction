"""Unit tests for extractor stage grade aggregation."""

import pytest
from unittest.mock import MagicMock

from education_agent.config.settings import Settings
from education_agent.pipeline.stages.extractor import ExtractorStage


class TestGradeAggregation:
    """Tests for grade aggregation from consolidated mark sheets."""

    @pytest.fixture
    def extractor_stage(self):
        settings = MagicMock(spec=Settings)
        return ExtractorStage(settings, llm_service=MagicMock())

    def test_aggregate_multiple_percentages(self, extractor_stage):
        """Test aggregating multiple semester percentages."""
        result = extractor_stage._aggregate_grades_from_text(
            "Multiple semester percentages: 63%, 57%, 62%"
        )
        assert result == 60.67  # (63 + 57 + 62) / 3

    def test_aggregate_decimal_percentages(self, extractor_stage):
        """Test aggregating percentages with decimals."""
        result = extractor_stage._aggregate_grades_from_text(
            "Sem 1: 75.5%, Sem 2: 80.5%"
        )
        assert result == 78.0

    def test_aggregate_gpas(self, extractor_stage):
        """Test aggregating GPA values."""
        result = extractor_stage._aggregate_grades_from_text(
            "SGPA: 7.5, 8.0, 7.2, 8.5"
        )
        assert result == 7.8

    def test_no_grades_found(self, extractor_stage):
        """Test when no numeric grades are found."""
        result = extractor_stage._aggregate_grades_from_text(
            "First Class with Distinction"
        )
        assert result is None

    def test_empty_string(self, extractor_stage):
        """Test with empty original value."""
        result = extractor_stage._aggregate_grades_from_text("")
        assert result is None

    def test_single_percentage(self, extractor_stage):
        """Test with a single percentage value."""
        result = extractor_stage._aggregate_grades_from_text("Overall: 75%")
        assert result == 75.0

    def test_single_gpa(self, extractor_stage):
        """Test with a single GPA value."""
        result = extractor_stage._aggregate_grades_from_text("CGPA: 8.5")
        assert result == 8.5

    def test_gpa_out_of_range_filtered(self, extractor_stage):
        """Test that GPA values outside 0-10 range are filtered."""
        result = extractor_stage._aggregate_grades_from_text(
            "Some text with 15.5 and 7.5 values"
        )
        # Only 7.5 should be included (15.5 is out of 0-10 range)
        assert result == 7.5

    def test_percentage_takes_priority_over_gpa(self, extractor_stage):
        """Test that percentages are matched first."""
        result = extractor_stage._aggregate_grades_from_text(
            "Score: 80% equivalent to 8.0 GPA"
        )
        # Should match the percentage first
        assert result == 80.0
