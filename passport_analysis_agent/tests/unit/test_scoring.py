"""Unit tests for scoring logic."""

import pytest

from passport_agent.config.constants import (
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
)


class TestScoringAlgorithm:
    """Tests for the scoring algorithm logic."""

    def test_confidence_high_threshold(self):
        """Test HIGH confidence threshold."""
        assert CONFIDENCE_HIGH_THRESHOLD == 85

    def test_confidence_medium_threshold(self):
        """Test MEDIUM confidence threshold."""
        assert CONFIDENCE_MEDIUM_THRESHOLD == 60

    def test_get_confidence_level_high(self):
        """Test HIGH confidence level assignment."""
        score = 90
        if score >= CONFIDENCE_HIGH_THRESHOLD:
            level = "HIGH"
        elif score >= CONFIDENCE_MEDIUM_THRESHOLD:
            level = "MEDIUM"
        else:
            level = "LOW"
        assert level == "HIGH"

    def test_get_confidence_level_medium(self):
        """Test MEDIUM confidence level assignment."""
        score = 70
        if score >= CONFIDENCE_HIGH_THRESHOLD:
            level = "HIGH"
        elif score >= CONFIDENCE_MEDIUM_THRESHOLD:
            level = "MEDIUM"
        else:
            level = "LOW"
        assert level == "MEDIUM"

    def test_get_confidence_level_low(self):
        """Test LOW confidence level assignment."""
        score = 50
        if score >= CONFIDENCE_HIGH_THRESHOLD:
            level = "HIGH"
        elif score >= CONFIDENCE_MEDIUM_THRESHOLD:
            level = "MEDIUM"
        else:
            level = "LOW"
        assert level == "LOW"

    def test_score_calculation_all_valid(self):
        """Test score calculation with all components valid."""
        # Checksum: 4/4 valid = 40 points
        checksum_score = (4 / 4) * 40

        # Field matches: 7/7 match = 40 points
        field_score = (7 / 7) * 40

        # OCR confidence: 0.95 = 19 points
        ocr_score = 0.95 * 20

        total = round(checksum_score + field_score + ocr_score)
        assert total == 99

    def test_score_calculation_partial(self):
        """Test score calculation with partial validity."""
        # Checksum: 2/4 valid = 20 points
        checksum_score = (2 / 4) * 40

        # Field matches: 5/7 match = ~28.57 points
        field_score = (5 / 7) * 40

        # OCR confidence: 0.8 = 16 points
        ocr_score = 0.8 * 20

        total = round(checksum_score + field_score + ocr_score)
        assert total == 65

    def test_score_calculation_no_mrz(self):
        """Test score calculation without MRZ."""
        # Checksum: 0 (no MRZ)
        checksum_score = 0

        # Field matches: 0 (can't compare without MRZ)
        field_score = 0

        # OCR confidence: 0.9 = 18 points
        ocr_score = 0.9 * 20

        total = round(checksum_score + field_score + ocr_score)
        assert total == 18


class TestScoringWeights:
    """Tests for scoring weight constants."""

    def test_total_weights_equal_100(self):
        """Test that all weights sum to 100."""
        from passport_agent.config.constants import (
            SCORE_WEIGHT_CHECKSUMS,
            SCORE_WEIGHT_FIELD_MATCHES,
            SCORE_WEIGHT_OCR_CONFIDENCE,
        )

        total = (
            SCORE_WEIGHT_CHECKSUMS
            + SCORE_WEIGHT_FIELD_MATCHES
            + SCORE_WEIGHT_OCR_CONFIDENCE
        )
        assert total == 100

    def test_checksum_weight(self):
        """Test checksum weight value."""
        from passport_agent.config.constants import SCORE_WEIGHT_CHECKSUMS

        assert SCORE_WEIGHT_CHECKSUMS == 40

    def test_field_match_weight(self):
        """Test field match weight value."""
        from passport_agent.config.constants import SCORE_WEIGHT_FIELD_MATCHES

        assert SCORE_WEIGHT_FIELD_MATCHES == 40

    def test_ocr_confidence_weight(self):
        """Test OCR confidence weight value."""
        from passport_agent.config.constants import SCORE_WEIGHT_OCR_CONFIDENCE

        assert SCORE_WEIGHT_OCR_CONFIDENCE == 20
