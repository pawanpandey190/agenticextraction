"""Grade conversion stage for converting grades to French 0-20 scale."""

from ...config.constants import DocumentType, GradingSystem
from ...config.settings import Settings
from ...models.credential_data import CredentialData
from ...models.grade_conversion import GradeConversionTable
from ...services.grade_table_service import GradeTableService
from ...utils.exceptions import GradeConversionError
from ..base import PipelineContext, PipelineStage


class GradeConverterStage(PipelineStage):
    """Stage for converting grades to French 0-20 scale."""

    def __init__(
        self,
        settings: Settings,
        grade_table_service: GradeTableService | None = None,
    ) -> None:
        super().__init__(settings)
        self.grade_table_service = grade_table_service

    @property
    def name(self) -> str:
        return "grade_converter"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Convert grade to French 0-20 scale for highest qualification only.

        Args:
            context: Pipeline context

        Returns:
            Updated context with converted grades

        Raises:
            GradeConversionError: If conversion fails critically
        """
        if not context.credentials:
            self.logger.warning("No credentials for grade conversion")
            return context

        # Get grade conversion table
        table = context.grade_conversion_table
        if table is None and self.grade_table_service:
            table = self.grade_table_service.get_table()

        if table is None:
            self.logger.warning("No grade conversion table available, using default")
            table = GradeTableService.create_default_table()

        # Find highest qualification credential considering the session's evaluation level
        highest_cred = self._find_highest_qualification_credential(
            context.credentials, context.evaluation_level
        )

        if not highest_cred:
            self.logger.warning("No credential found for grade conversion")
            context.set_stage_result(self.name, {
                "conversions_attempted": 0,
                "conversions_successful": 0,
                "table_version": table.version if table else None,
                "reason": "No degree credential found",
            })
            return context

        if not highest_cred.final_grade:
            self.logger.warning(
                f"Highest qualification {highest_cred.source_file} has no grade"
            )
            context.set_stage_result(self.name, {
                "conversions_attempted": 0,
                "conversions_successful": 0,
                "table_version": table.version if table else None,
                "reason": "Highest qualification has no grade",
            })
            return context

        try:
            # Aggregate semesters if final grade is missing or zero
            if highest_cred.final_grade.numeric_value is None or highest_cred.final_grade.numeric_value == 0:
                self._aggregate_semester_grades(highest_cred, context.credentials)

            grade = highest_cred.final_grade

            # Allow conversion if we have either a numeric value OR a letter grade string
            can_convert = (
                grade.numeric_value is not None or
                (grade.grading_system in [GradingSystem.LETTER_GRADE, GradingSystem.UK_HONORS] and grade.original_value)
            )

            if not can_convert:
                self.logger.warning(
                    f"Insufficient grade data for {highest_cred.source_file} after aggregation, skipping conversion"
                )
                context.set_stage_result(self.name, {
                    "conversions_attempted": 1,
                    "conversions_successful": 0,
                    "table_version": table.version if table else None,
                    "credential_converted": highest_cred.source_file,
                    "reason": "Insufficient grade data (no numeric or letter grade)",
                })
                return context

            # ── THRESHOLD-BASED FRENCH EQUIVALENCE ─────────────────────────────
            # Look up country-specific threshold; compare student score to it.
            # Result: 8.0 = PASS (≥ 8/20), 4.0 = FAIL (< 8/20)

            country_system = table.get_country_system(highest_cred.country) if highest_cred.country else None

            if country_system:
                meets_threshold, reason = country_system.check_threshold(
                    numeric_value=grade.numeric_value,
                    grading_system=grade.grading_system.value if grade.grading_system else "OTHER",
                    max_possible=grade.max_possible,
                    original_value=grade.original_value,
                )
                french_equivalent = 8.0 if meets_threshold else 4.0
            else:
                # No country config — try a generic threshold check via formula
                from ...models.grade_conversion import normalize_to_quality_pct
                normalized = normalize_to_quality_pct(
                    grade.numeric_value,
                    grade.grading_system.value if grade.grading_system else "OTHER",
                    grade.max_possible,
                )
                if normalized is not None:
                    meets_threshold = normalized >= 40.0  # Generic 40% = 8/20 threshold
                    french_equivalent = 8.0 if meets_threshold else 4.0
                    reason = (
                        f"{normalized:.1f}% {'≥' if meets_threshold else '<'} 40% "
                        f"(generic threshold, no country-specific config found) → "
                        f"{'≥' if meets_threshold else '<'} 8/20."
                    )
                else:
                    french_equivalent = None
                    reason = "Could not evaluate grade — insufficient data."

            if french_equivalent is not None:
                grade.french_scale_equivalent = french_equivalent
                grade.conversion_notes = reason

                context.set_stage_result(self.name, {
                    "conversions_attempted": 1,
                    "conversions_successful": 1,
                    "table_version": table.version if table else None,
                    "credential_converted": highest_cred.source_file,
                    "original_grade": grade.original_value,
                    "french_equivalent": french_equivalent,
                    "threshold_met": french_equivalent >= 8.0,
                    "reason": reason,
                })

                self.logger.info(
                    "Grade threshold evaluated",
                    file=highest_cred.source_file,
                    original=grade.original_value,
                    french_equivalent=french_equivalent,
                    threshold_met=french_equivalent >= 8.0,
                )
            else:
                grade.conversion_notes = "Threshold evaluation not possible — no grade data."
                context.metadata.add_flag(f"CONVERSION_NOT_POSSIBLE: {highest_cred.source_file}")
                context.set_stage_result(self.name, {
                    "conversions_attempted": 1,
                    "conversions_successful": 0,
                    "table_version": table.version if table else None,
                    "credential_converted": highest_cred.source_file,
                    "reason": "Conversion not possible",
                })
                self.logger.warning(
                    "Grade threshold evaluation not possible",
                    file=highest_cred.source_file,
                    grading_system=grade.grading_system.value if grade.grading_system else None,
                    country=highest_cred.country,
                )

        except Exception as e:
            self.logger.error(
                "Grade conversion failed",
                file=highest_cred.source_file,
                error=str(e),
            )
            highest_cred.final_grade.conversion_notes = f"Conversion failed: {e}"
            context.metadata.add_error(
                f"Grade conversion failed for {highest_cred.source_file}: {e}"
            )
            context.set_stage_result(self.name, {
                "conversions_attempted": 1,
                "conversions_successful": 0,
                "table_version": table.version if table else None,
                "credential_converted": highest_cred.source_file,
                "error": str(e),
            })

        return context

    def _find_highest_qualification_credential(
        self, credentials: list[CredentialData], evaluation_level: str | None = None
    ) -> CredentialData | None:
        """Find the credential with the highest academic level and best document type,
        considering the admission/evaluation level requested.

        Args:
            credentials: List of CredentialData objects
            evaluation_level: The target admission level (e.g., "bachelors", "masters")

        Returns:
            The highest qualification credential or None
        """
        # Define document type priority (higher is better)
        type_priority = {
            DocumentType.CONSOLIDATED_MARK_SHEET: 10,
            DocumentType.TRANSCRIPT: 9,
            DocumentType.DEGREE_CERTIFICATE: 8,
            DocumentType.MARK_SHEET: 7,
            DocumentType.PROVISIONAL_CERTIFICATE: 6,
            DocumentType.DIPLOMA: 5,
            DocumentType.SEMESTER_MARK_SHEET: 4,
        }

        # Filter to documents that can represent a qualification
        qualification_creds = [
            c for c in credentials
            if c.academic_level is not None and c.academic_level.rank > 0
        ]

        if not qualification_creds:
            return None

        # Determine "Target Rank" based on Evaluation Level
        # schooling -> Rank 1 (Secondary)
        # bachelors -> Rank 1 (Secondary) (since you need Secondary to enter Bachelors)
        # masters   -> Rank 3 (Bachelor)  (since you need Bachelors to enter Masters)
        target_rank = 0
        if evaluation_level == "schooling":
            target_rank = 1
        elif evaluation_level == "bachelors":
            target_rank = 1  # We evaluate the Secondary certificate for Bachelors admission
        elif evaluation_level == "masters":
            target_rank = 3  # We evaluate the Bachelors degree for Masters admission

        def get_relevance_score(c: CredentialData) -> int:
            """Prioritize the target rank, but don't ignore higher ranks if they exist."""
            rank = c.academic_level.rank
            if target_rank > 0:
                if rank == target_rank:
                    return 100  # Perfect match for admission level
                elif rank > target_rank:
                    return 50  # Higher than target, still relevant
                else:
                    return rank  # Lower than target
            return rank

        # Sort primarily by relevance, then by academic level rank, then by type priority
        qualification_creds.sort(
            key=lambda c: (
                get_relevance_score(c),
                c.academic_level.rank,
                type_priority.get(c.document_type, 0),
                c.confidence_score
            ),
            reverse=True
        )

        return qualification_creds[0]
        
        return qualification_creds[0]

    def _aggregate_semester_grades(self, target: CredentialData, all_credentials: list[CredentialData]) -> None:
        """Aggregate grades from semester mark sheets if final grade is missing.
        
        Args:
            target: The credential object to update with aggregated grade
            all_credentials: All extracted credentials to search for semesters
        """
        if not target.academic_level:
            return

        # Find all mark sheets for the same academic level and qualification
        semesters = [
            c for c in all_credentials
            if (c.document_type == DocumentType.SEMESTER_MARK_SHEET or c.document_type == DocumentType.MARK_SHEET)
            and c.academic_level == target.academic_level
            and c.final_grade is not None
            and c.final_grade.numeric_value is not None
        ]

        if not semesters:
            return

        # Simple average of all found semester/yearly grades
        total_value = sum(s.final_grade.numeric_value for s in semesters)
        count = len(semesters)
        
        if count > 0:
            avg_value = total_value / count
            
            # Update target's final grade info
            from ...models.credential_data import GradeInfo
            
            # Use the grading system from the first semester sheet found
            source_system = semesters[0].final_grade.grading_system
            source_max = semesters[0].final_grade.max_possible
            
            if not target.final_grade:
                target.final_grade = GradeInfo(
                    grading_system=source_system,
                    max_possible=source_max
                )
            
            target.final_grade.numeric_value = round(avg_value, 2)
            target.final_grade.original_value = f"{avg_value:.2f} (Average of {count} records)"
            target.final_grade.grading_system = source_system
            target.final_grade.max_possible = source_max
            
            self.logger.info(
                "Aggregated semester grades",
                file=target.source_file,
                avg_value=avg_value,
                count=count,
                system=source_system.value
            )

    def _convert_grade(
        self,
        grade,
        country: str | None,
        table: GradeConversionTable,
    ) -> float | None:
        """Convert a grade to French 0-20 scale.

        Args:
            grade: GradeInfo object
            country: Country code
            table: Grade conversion table

        Returns:
            French scale equivalent (0-20) or None if conversion not possible
        """
        numeric_value = grade.numeric_value
        grading_system = grade.grading_system

        # For letter-based systems, we can proceed even without a numeric value
        if numeric_value is None and grading_system not in [GradingSystem.LETTER_GRADE, GradingSystem.UK_HONORS]:
            # Last resort: try original_value as a float
            if grade.original_value:
                try:
                    numeric_value = float(grade.original_value.replace('%', '').strip())
                    self.logger.warning(
                        "numeric_value was None, parsed from original_value",
                        original=grade.original_value,
                        parsed=numeric_value,
                    )
                except (ValueError, AttributeError):
                    return None
            else:
                return None

        # Cap percentage at 100
        if grading_system == GradingSystem.PERCENTAGE:
            numeric_value = min(numeric_value, 100.0)
            return table.convert_percentage(numeric_value, country)

        elif grading_system == GradingSystem.GPA_4:
            return table.convert_gpa_4(numeric_value, country)

        elif grading_system == GradingSystem.GPA_10:
            return table.convert_gpa_10(numeric_value, country)

        elif grading_system == GradingSystem.LETTER_GRADE:
            # Try country-specific first, then fall back to US letter grades (most universal)
            result = table.convert_letter(grade.original_value, country)
            if result is None:
                result = table.convert_letter(grade.original_value, "US")
            return result

        elif grading_system == GradingSystem.UK_HONORS:
            result = table.convert_letter(grade.original_value, country or "GB")
            if result is None:
                result = table.convert_letter(grade.original_value, "GB")
            return result

        elif grading_system == GradingSystem.GERMAN_5:
            # German grades: 1.0-5.0 where 1.0 is best
            # Use formula directly: ((5 - grade) / 4) * 20
            val = max(1.0, min(5.0, numeric_value))
            return round(((5.0 - val) / 4.0) * 20.0, 2)

        elif grading_system == GradingSystem.FRENCH_20:
            # Already on French scale
            return round(numeric_value, 2)

        else:
            # GradingSystem.OTHER — try intelligent fallback
            # 1. If max_possible is known, use universal formula
            if grade.max_possible and grade.max_possible > 0:
                return round((numeric_value / grade.max_possible) * 20.0, 2)

            # 2. If value is in percentage range (0–100), treat as percentage
            if 0 <= numeric_value <= 100:
                return table.convert_percentage(numeric_value, country)

            # 3. If value looks like a 4.0 GPA
            if 0 <= numeric_value <= 4.0:
                return table.convert_gpa_4(numeric_value, country)

            return None


def convert_grade_to_french(
    original_value: str,
    numeric_value: float,
    grading_system: GradingSystem,
    country: str | None,
    table: GradeConversionTable,
) -> float | None:
    """Standalone function to convert a grade to French scale.

    Args:
        original_value: Original grade string
        numeric_value: Numeric value of the grade
        grading_system: Grading system
        country: Country code (ISO 3166-1 alpha-2)
        table: Grade conversion table

    Returns:
        French scale equivalent (0-20) or None if conversion not possible
    """
    # Cap percentage at 100
    if grading_system == GradingSystem.PERCENTAGE:
        numeric_value = min(numeric_value, 100.0)
        return table.convert_percentage(numeric_value, country)

    elif grading_system == GradingSystem.GPA_4:
        return table.convert_gpa_4(numeric_value, country)

    elif grading_system == GradingSystem.GPA_10:
        return table.convert_gpa_10(numeric_value, country)

    elif grading_system == GradingSystem.LETTER_GRADE:
        return table.convert_letter(original_value, country)

    elif grading_system == GradingSystem.UK_HONORS:
        return table.convert_letter(original_value, country or "GB")

    elif grading_system == GradingSystem.GERMAN_5:
        # German grades: 1.0-5.0 where 1.0 is best
        # Use formula directly: ((5 - grade) / 4) * 20
        val = max(1.0, min(5.0, numeric_value))
        return round(((5.0 - val) / 4.0) * 20.0, 2)

    elif grading_system == GradingSystem.FRENCH_20:
        return numeric_value

    else:
        if 0 <= numeric_value <= 100:
            return table.convert_percentage(numeric_value, country)
        return None
