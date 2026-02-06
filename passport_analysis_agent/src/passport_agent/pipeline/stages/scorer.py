"""Scorer pipeline stage."""

from ...config.constants import (
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    SCORE_WEIGHT_CHECKSUMS,
    SCORE_WEIGHT_FIELD_MATCHES,
    SCORE_WEIGHT_OCR_CONFIDENCE,
)
from ...models.passport_data import VisualPassportData
from ...models.result import PassportAnalysisResult
from ..base import PipelineContext, PipelineStage


class ScorerStage(PipelineStage):
    """Stage 7: Calculate accuracy score and confidence level."""

    @property
    def name(self) -> str:
        return "Scorer"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Calculate final accuracy score and build result.

        Scoring formula:
        - Checksum validity: 40 points (10 per checksum)
        - Field matches: 40 points (split across 7 fields)
        - OCR confidence: 20 points

        Args:
            context: Pipeline context

        Returns:
            Updated context with final result
        """
        # Calculate components
        checksum_score = self._calculate_checksum_score(context)
        field_match_score = self._calculate_field_match_score(context)
        ocr_score = self._calculate_ocr_score(context)

        # Total score
        total_score = round(checksum_score + field_match_score + ocr_score)
        total_score = max(0, min(100, total_score))  # Clamp to 0-100

        # Determine confidence level
        confidence_level = self._get_confidence_level(total_score)

        # Build field comparison dict
        field_comparison = {}
        if context.cross_validation:
            field_comparison = context.cross_validation.to_field_dict()

        # Build checksum validation dict
        mrz_checksum_validation = {}
        if context.mrz_data:
            mrz_checksum_validation = context.mrz_data.checksum_results.to_dict()

        # Build final result
        result = PassportAnalysisResult(
            extracted_passport_data=context.visual_data or VisualPassportData(),
            extracted_mrz_data=context.mrz_data,
            field_comparison=field_comparison,
            mrz_checksum_validation=mrz_checksum_validation,
            accuracy_score=total_score,
            confidence_level=confidence_level,
            processing_errors=context.metadata.errors.copy(),
            processing_warnings=context.metadata.warnings.copy(),
            source_file=context.file_path,
            processing_time_seconds=context.metadata.processing_time_seconds,
        )

        context.final_result = result
        context.metadata.mark_completed()

        # Update processing time in result
        result.processing_time_seconds = context.metadata.processing_time_seconds

        self.logger.info(
            "Scoring complete",
            accuracy_score=total_score,
            confidence_level=confidence_level,
            checksum_score=checksum_score,
            field_match_score=field_match_score,
            ocr_score=ocr_score,
        )

        context.set_stage_result(
            self.name,
            {
                "accuracy_score": total_score,
                "confidence_level": confidence_level,
                "checksum_score": checksum_score,
                "field_match_score": field_match_score,
                "ocr_score": ocr_score,
            },
        )

        return context

    def _calculate_checksum_score(self, context: PipelineContext) -> float:
        """Calculate score component from MRZ checksums.

        Args:
            context: Pipeline context

        Returns:
            Score (0 to SCORE_WEIGHT_CHECKSUMS)
        """
        if context.mrz_data is None:
            return 0.0

        checksums = context.mrz_data.checksum_results
        valid_count = checksums.valid_count
        total_checksums = 4  # passport_number, dob, expiry, composite

        return (valid_count / total_checksums) * SCORE_WEIGHT_CHECKSUMS

    def _calculate_field_match_score(self, context: PipelineContext) -> float:
        """Calculate score component from field matches.

        Args:
            context: Pipeline context

        Returns:
            Score (0 to SCORE_WEIGHT_FIELD_MATCHES)
        """
        if context.cross_validation is None:
            return 0.0

        validation = context.cross_validation
        if validation.total_fields == 0:
            return 0.0

        # Only count comparable fields (not skipped)
        comparable = validation.total_fields - validation.skipped_fields
        if comparable == 0:
            return 0.0

        match_ratio = validation.matched_fields / comparable
        return match_ratio * SCORE_WEIGHT_FIELD_MATCHES

    def _calculate_ocr_score(self, context: PipelineContext) -> float:
        """Calculate score component from OCR confidence.

        Args:
            context: Pipeline context

        Returns:
            Score (0 to SCORE_WEIGHT_OCR_CONFIDENCE)
        """
        if context.visual_data is None:
            return 0.0

        confidence = context.visual_data.ocr_confidence
        return confidence * SCORE_WEIGHT_OCR_CONFIDENCE

    def _get_confidence_level(self, score: int) -> str:
        """Determine confidence level from score.

        Args:
            score: Accuracy score (0-100)

        Returns:
            Confidence level string
        """
        if score >= CONFIDENCE_HIGH_THRESHOLD:
            return "HIGH"
        elif score >= CONFIDENCE_MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "LOW"
