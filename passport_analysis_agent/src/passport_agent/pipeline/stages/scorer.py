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
            remarks=self._generate_remarks(total_score, confidence_level, context)
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

    def _generate_remarks(self, score: int, confidence: str, context: PipelineContext) -> str:
        """Generate a human-readable summary of the analysis.

        Args:
            score: Overall accuracy score
            confidence: Confidence level
            context: Pipeline context

        Returns:
            Reasoning string
        """
        reasons = []
        
        # 1. Overall Score & Confidence
        reasons.append(f"Passport analysis completed with an accuracy score of {score}/100 ({confidence} confidence).")

        # 2. MRZ Validation
        if context.mrz_data:
            checksums = context.mrz_data.checksum_results
            if checksums.composite:
                reasons.append("MRZ data was successfully detected and all primary checksums (Date of Birth, Expiry Date, Passport Number) were validated as correct.")
            else:
                valid_parts = []
                if checksums.date_of_birth: valid_parts.append("DOB")
                if checksums.expiry_date: valid_parts.append("Expiry")
                if checksums.passport_number: valid_parts.append("Passport Number")
                
                if valid_parts:
                    reasons.append(f"MRZ was detected with partial validity (Valid: {', '.join(valid_parts)}). Some checksums failed validation.")
                else:
                    reasons.append("MRZ was detected but failed all checksum validations.")
        else:
            reasons.append("MRZ (Machine Readable Zone) could not be reliably detected on this document.")

        # 3. Cross-Validation
        if context.cross_validation:
            cv = context.cross_validation
            if cv.mismatched_fields == 0 and cv.matched_fields > 0:
                reasons.append("All visual data fields (Name, DOB, Passport Number, etc.) perfectly match the data encoded in the MRZ region.")
            elif cv.matched_fields > 0:
                reasons.append(f"Most visual fields match the MRZ data, however {cv.mismatched_fields} discrepancy(ies) were found.")
            else:
                reasons.append("Significant discrepancies found between visual data and MRZ encoded data.")

        # 4. Image Quality
        if context.visual_data and context.visual_data.ocr_confidence < 0.7:
             reasons.append("The document image quality or clarity may be low, resulting in lower OCR confidence for some fields.")

        return " ".join(reasons)
