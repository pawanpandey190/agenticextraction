"""Final result model for passport analysis."""

from typing import Literal

from pydantic import BaseModel, Field

from .mrz import MRZData
from .passport_data import VisualPassportData


class PassportAnalysisResult(BaseModel):
    """Final output model for passport analysis.

    Contains all extracted data, validation results, and scoring.
    """

    # Extracted data
    extracted_passport_data: VisualPassportData = Field(
        description="Data extracted from visual inspection zone"
    )
    extracted_mrz_data: MRZData | None = Field(
        default=None, description="Data parsed from MRZ (if found)"
    )

    # Validation results
    field_comparison: dict[str, Literal["match", "mismatch"]] = Field(
        default_factory=dict, description="Visual vs MRZ field comparison results"
    )
    mrz_checksum_validation: dict[str, bool] = Field(
        default_factory=dict, description="MRZ checksum validation results"
    )

    # Scoring
    accuracy_score: int = Field(
        default=0, ge=0, le=100, description="Overall accuracy score (0-100)"
    )
    confidence_level: Literal["LOW", "MEDIUM", "HIGH"] = Field(
        default="LOW", description="Confidence level based on score"
    )

    # Errors and warnings
    processing_errors: list[str] = Field(
        default_factory=list, description="List of errors encountered during processing"
    )
    processing_warnings: list[str] = Field(
        default_factory=list, description="List of warnings from processing"
    )

    # Assessment summary
    remarks: str = Field(
        default="", description="Summary of analysis results and justifications"
    )

    # Metadata
    source_file: str | None = Field(
        default=None, description="Path to source file processed"
    )
    processing_time_seconds: float | None = Field(
        default=None, description="Total processing time in seconds"
    )

    model_config = {"extra": "forbid"}

    @property
    def is_valid(self) -> bool:
        """Check if the analysis result is valid (no critical errors)."""
        return len(self.processing_errors) == 0 and self.accuracy_score > 0

    @property
    def has_mrz(self) -> bool:
        """Check if MRZ data was successfully extracted."""
        return self.extracted_mrz_data is not None

    @property
    def all_checksums_valid(self) -> bool:
        """Check if all MRZ checksums are valid."""
        if not self.mrz_checksum_validation:
            return False
        return all(self.mrz_checksum_validation.values())

    @property
    def all_fields_match(self) -> bool:
        """Check if all compared fields match."""
        if not self.field_comparison:
            return False
        return all(v == "match" for v in self.field_comparison.values())

    def to_summary(self) -> dict:
        """Get a summary of the analysis result."""
        return {
            "accuracy_score": self.accuracy_score,
            "confidence_level": self.confidence_level,
            "has_mrz": self.has_mrz,
            "all_checksums_valid": self.all_checksums_valid,
            "all_fields_match": self.all_fields_match,
            "error_count": len(self.processing_errors),
            "warning_count": len(self.processing_warnings),
        }
