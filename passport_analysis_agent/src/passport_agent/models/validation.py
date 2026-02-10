"""Validation and comparison models."""

from typing import Literal

from pydantic import BaseModel, Field


class FieldComparison(BaseModel):
    """Result of comparing a single field between visual and MRZ data."""

    field_name: str = Field(description="Name of the field compared")
    visual_value: str | None = Field(
        default=None, description="Value from visual extraction"
    )
    mrz_value: str | None = Field(default=None, description="Value from MRZ")
    match_result: Literal["match", "mismatch"] = Field(
        description="Whether the values match"
    )
    similarity_score: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Similarity score for fuzzy matches"
    )
    match_type: Literal["exact", "fuzzy", "skipped"] = Field(
        default="exact", description="Type of matching used"
    )

    model_config = {"extra": "forbid"}


class CrossValidationResult(BaseModel):
    """Result of cross-validating visual data against MRZ data."""

    field_comparisons: list[FieldComparison] = Field(
        default_factory=list, description="Individual field comparison results"
    )
    total_fields: int = Field(default=0, description="Total fields compared")
    matched_fields: int = Field(default=0, description="Number of matching fields")
    mismatched_fields: int = Field(
        default=0, description="Number of mismatched fields"
    )
    skipped_fields: int = Field(
        default=0, description="Number of fields skipped due to missing data"
    )

    model_config = {"extra": "forbid"}

    def add_comparison(self, comparison: FieldComparison) -> None:
        """Add a field comparison result."""
        self.field_comparisons.append(comparison)
        self.total_fields += 1
        if comparison.match_type == "skipped":
            self.skipped_fields += 1
        elif comparison.match_result == "match":
            self.matched_fields += 1
        else:
            self.mismatched_fields += 1

    def to_field_dict(self) -> dict[str, Literal["match", "mismatch"]]:
        """Convert to simple field -> result dictionary."""
        return {
            comp.field_name: comp.match_result
            for comp in self.field_comparisons
            if comp.match_type != "skipped"
        }

    @property
    def match_ratio(self) -> float:
        """Get the ratio of matched fields to total fields."""
        comparable_fields = self.total_fields - self.skipped_fields
        if comparable_fields == 0:
            return 0.0
        return self.matched_fields / comparable_fields

    @property
    def all_match(self) -> bool:
        """Check if all comparable fields match."""
        return self.mismatched_fields == 0 and self.matched_fields > 0
