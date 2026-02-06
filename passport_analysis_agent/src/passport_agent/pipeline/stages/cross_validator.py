"""Cross-validator pipeline stage."""

from ...config.constants import (
    CROSS_VALIDATION_FIELDS,
    EXACT_MATCH_FIELDS,
    FUZZY_MATCH_FIELDS,
)
from ...models.validation import CrossValidationResult, FieldComparison
from ...utils.fuzzy_match import exact_match, fuzzy_match
from ..base import PipelineContext, PipelineStage


class CrossValidatorStage(PipelineStage):
    """Stage 6: Cross-validate visual data against MRZ data."""

    @property
    def name(self) -> str:
        return "CrossValidator"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Compare visual extraction with MRZ data.

        Uses fuzzy matching for names, exact matching for other fields.

        Args:
            context: Pipeline context

        Returns:
            Updated context with validation results
        """
        validation = CrossValidationResult()

        # If no MRZ data, skip comparison
        if context.mrz_data is None:
            context.add_warning("No MRZ data for cross-validation")
            context.cross_validation = validation
            context.set_stage_result(
                self.name, {"compared": False, "reason": "no_mrz"}
            )
            return context

        # If no visual data, skip comparison
        if context.visual_data is None:
            context.add_warning("No visual data for cross-validation")
            context.cross_validation = validation
            context.set_stage_result(
                self.name, {"compared": False, "reason": "no_visual"}
            )
            return context

        visual = context.visual_data
        mrz = context.mrz_data

        for field_name in CROSS_VALIDATION_FIELDS:
            comparison = self._compare_field(field_name, visual, mrz)
            validation.add_comparison(comparison)

        context.cross_validation = validation

        self.logger.info(
            "Cross-validation complete",
            total_fields=validation.total_fields,
            matched=validation.matched_fields,
            mismatched=validation.mismatched_fields,
            skipped=validation.skipped_fields,
            match_ratio=validation.match_ratio,
        )

        context.set_stage_result(
            self.name,
            {
                "compared": True,
                "matched": validation.matched_fields,
                "mismatched": validation.mismatched_fields,
                "skipped": validation.skipped_fields,
            },
        )

        return context

    def _compare_field(self, field_name: str, visual, mrz) -> FieldComparison:
        """Compare a single field between visual and MRZ data.

        Args:
            field_name: Name of the field to compare
            visual: Visual passport data
            mrz: MRZ data

        Returns:
            FieldComparison result
        """
        visual_value = self._get_field_value(visual, field_name)
        mrz_value = self._get_mrz_field_value(mrz, field_name)

        # Handle missing values
        if visual_value is None or mrz_value is None:
            return FieldComparison(
                field_name=field_name,
                visual_value=visual_value,
                mrz_value=mrz_value,
                match_result="mismatch",
                similarity_score=0.0,
                match_type="skipped",
            )

        # Determine match type
        if field_name in FUZZY_MATCH_FIELDS:
            is_match, score = fuzzy_match(
                visual_value,
                mrz_value,
                threshold=self.settings.fuzzy_match_threshold,
            )
            return FieldComparison(
                field_name=field_name,
                visual_value=visual_value,
                mrz_value=mrz_value,
                match_result="match" if is_match else "mismatch",
                similarity_score=score,
                match_type="fuzzy",
            )
        else:
            # Exact match
            is_match = exact_match(visual_value, mrz_value)
            return FieldComparison(
                field_name=field_name,
                visual_value=visual_value,
                mrz_value=mrz_value,
                match_result="match" if is_match else "mismatch",
                similarity_score=1.0 if is_match else 0.0,
                match_type="exact",
            )

    def _get_field_value(self, visual, field_name: str) -> str | None:
        """Get field value from visual data as string.

        Args:
            visual: VisualPassportData
            field_name: Field name

        Returns:
            String value or None
        """
        value = getattr(visual, field_name, None)
        if value is None:
            return None
        if hasattr(value, "isoformat"):  # date
            return value.isoformat()
        return str(value)

    def _get_mrz_field_value(self, mrz, field_name: str) -> str | None:
        """Get field value from MRZ data as string.

        Args:
            mrz: MRZData
            field_name: Field name

        Returns:
            String value or None
        """
        # Map visual field names to MRZ field names
        field_map = {
            "expiry_date": "expiry_date",
            "date_of_birth": "date_of_birth",
            "first_name": "first_name",
            "last_name": "last_name",
            "passport_number": "passport_number",
            "sex": "sex",
            "issuing_country": "issuing_country",
        }

        mrz_field = field_map.get(field_name, field_name)
        value = getattr(mrz, mrz_field, None)

        if value is None:
            return None
        if hasattr(value, "isoformat"):  # date
            return value.isoformat()
        return str(value)
