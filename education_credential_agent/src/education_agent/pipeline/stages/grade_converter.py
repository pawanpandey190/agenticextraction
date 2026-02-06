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

        # Find highest qualification credential
        highest_cred = self._find_highest_qualification_credential(context.credentials)

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

        if highest_cred.final_grade.numeric_value is None:
            self.logger.warning(
                f"No numeric grade value for {highest_cred.source_file}, skipping conversion"
            )
            context.set_stage_result(self.name, {
                "conversions_attempted": 1,
                "conversions_successful": 0,
                "table_version": table.version if table else None,
                "credential_converted": highest_cred.source_file,
                "reason": "No numeric grade value",
            })
            return context

        try:
            french_equivalent = self._convert_grade(
                grade=highest_cred.final_grade,
                country=highest_cred.country,
                table=table,
            )

            if french_equivalent is not None:
                highest_cred.final_grade.french_scale_equivalent = french_equivalent
                highest_cred.final_grade.conversion_notes = (
                    f"Converted from {highest_cred.final_grade.grading_system.value} "
                    f"using {'country-specific' if highest_cred.country else 'default'} rules"
                )

                context.set_stage_result(self.name, {
                    "conversions_attempted": 1,
                    "conversions_successful": 1,
                    "table_version": table.version if table else None,
                    "credential_converted": highest_cred.source_file,
                    "original_grade": highest_cred.final_grade.original_value,
                    "french_equivalent": french_equivalent,
                })

                self.logger.info(
                    "Grade converted for highest qualification",
                    file=highest_cred.source_file,
                    original=highest_cred.final_grade.original_value,
                    french_equivalent=french_equivalent,
                )
            else:
                highest_cred.final_grade.conversion_notes = "Conversion Not Possible"
                context.metadata.add_flag(
                    f"CONVERSION_NOT_POSSIBLE: {highest_cred.source_file}"
                )
                context.set_stage_result(self.name, {
                    "conversions_attempted": 1,
                    "conversions_successful": 0,
                    "table_version": table.version if table else None,
                    "credential_converted": highest_cred.source_file,
                    "reason": "Conversion not possible",
                })
                self.logger.warning(
                    "Grade conversion not possible",
                    file=highest_cred.source_file,
                    grading_system=highest_cred.final_grade.grading_system.value,
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
        self, credentials: list[CredentialData]
    ) -> CredentialData | None:
        """Find the credential with the highest academic level.

        Args:
            credentials: List of CredentialData objects

        Returns:
            The highest qualification credential or None
        """
        degree_creds = [
            c for c in credentials
            if c.document_type in (
                DocumentType.DEGREE_CERTIFICATE,
                DocumentType.PROVISIONAL_CERTIFICATE,
                DocumentType.DIPLOMA,
                DocumentType.CONSOLIDATED_MARK_SHEET,
            )
            and c.academic_level is not None
        ]

        if not degree_creds:
            return None

        # Sort by academic level rank (highest first)
        degree_creds.sort(key=lambda c: c.academic_level.rank, reverse=True)
        return degree_creds[0]

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
        if numeric_value is None:
            return None

        grading_system = grade.grading_system

        # Cap percentage at 100
        if grading_system == GradingSystem.PERCENTAGE:
            numeric_value = min(numeric_value, 100.0)
            return table.convert_percentage(numeric_value, country)

        elif grading_system == GradingSystem.GPA_4:
            return table.convert_gpa_4(numeric_value, country)

        elif grading_system == GradingSystem.GPA_10:
            return table.convert_gpa_10(numeric_value, country)

        elif grading_system == GradingSystem.LETTER_GRADE:
            return table.convert_letter(grade.original_value, country)

        elif grading_system == GradingSystem.UK_HONORS:
            return table.convert_letter(grade.original_value, country or "GB")

        elif grading_system == GradingSystem.GERMAN_5:
            # German grades: 1.0-5.0 where 1.0 is best
            country_system = table.get_country_system("DE")
            if country_system:
                return country_system.convert_numeric(numeric_value)
            return None

        elif grading_system == GradingSystem.FRENCH_20:
            # Already on French scale
            return numeric_value

        else:
            # Try to convert as percentage if in 0-100 range
            if 0 <= numeric_value <= 100:
                return table.convert_percentage(numeric_value, country)

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
        country_system = table.get_country_system("DE")
        if country_system:
            return country_system.convert_numeric(numeric_value)
        return None

    elif grading_system == GradingSystem.FRENCH_20:
        return numeric_value

    else:
        if 0 <= numeric_value <= 100:
            return table.convert_percentage(numeric_value, country)
        return None
