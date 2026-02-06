"""Semester validation stage for Bachelor's degrees."""

from ...config.constants import AcademicLevel, BACHELOR_SEMESTER_MAP, DocumentType
from ...config.settings import Settings
from ...models.credential_data import BachelorValidation, SemesterRecord
from ...utils.exceptions import ValidationError
from ..base import PipelineContext, PipelineStage


class SemesterValidatorStage(PipelineStage):
    """Stage for validating Bachelor's degree semester completeness."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    @property
    def name(self) -> str:
        return "semester_validator"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Validate semester completeness for Bachelor's degrees.

        Args:
            context: Pipeline context

        Returns:
            Updated context with validation results

        Raises:
            ValidationError: If validation fails critically
        """
        if not context.credentials:
            self.logger.warning("No credentials to validate")
            return context

        # Find Bachelor's degree credentials
        bachelor_credentials = [
            c for c in context.credentials
            if c.academic_level == AcademicLevel.BACHELOR
        ]

        if not bachelor_credentials:
            self.logger.info("No Bachelor's degrees found, skipping semester validation")
            context.set_stage_result(self.name, {
                "validation_applied": False,
                "reason": "No Bachelor's degrees found",
            })
            return context

        # Determine expected semesters from the Bachelor's degree
        expected_semesters = self._get_expected_semesters(bachelor_credentials)

        # Check for consolidated mark sheet first
        consolidated_mark_sheets = [
            c for c in context.credentials
            if c.document_type == DocumentType.CONSOLIDATED_MARK_SHEET
            and c.academic_level == AcademicLevel.BACHELOR
        ]

        if consolidated_mark_sheets:
            # Mark as complete via consolidated
            validation = BachelorValidation(
                expected_semesters=expected_semesters,
                semesters_found=list(range(1, expected_semesters + 1)),
                semesters_missing=[],
                is_complete=True,
                has_consolidated_mark_sheet=True,
                notes="Complete via consolidated mark sheet",
            )
            context.set_stage_result(self.name, {
                "validation_applied": True,
                "has_consolidated_mark_sheet": True,
                "expected_semesters": expected_semesters,
                "found_semesters": validation.semesters_found,
                "missing_semesters": [],
                "is_complete": True,
            })

            self.logger.info(
                "Semester validation completed via consolidated mark sheet",
                expected_semesters=expected_semesters,
            )

            return context

        # Check for transcripts with final grades at Bachelor level
        # International transcripts containing complete academic records
        # should be treated as equivalent to consolidated mark sheets
        transcripts_with_grades = [
            c for c in context.credentials
            if c.document_type == DocumentType.TRANSCRIPT
            and c.academic_level == AcademicLevel.BACHELOR
            and c.final_grade is not None
        ]

        if transcripts_with_grades:
            # Treat transcript with final grade as equivalent to consolidated
            validation = BachelorValidation(
                expected_semesters=expected_semesters,
                semesters_found=list(range(1, expected_semesters + 1)),
                semesters_missing=[],
                is_complete=True,
                has_consolidated_mark_sheet=False,
                notes="Complete via transcript with final grade",
            )
            context.set_stage_result(self.name, {
                "validation_applied": True,
                "has_consolidated_mark_sheet": False,
                "has_transcript_with_grade": True,
                "expected_semesters": expected_semesters,
                "found_semesters": validation.semesters_found,
                "missing_semesters": [],
                "is_complete": True,
            })

            self.logger.info(
                "Semester validation completed via transcript with final grade",
                expected_semesters=expected_semesters,
                transcript_count=len(transcripts_with_grades),
            )

            return context

        # Find semester mark sheets for Bachelor's level only
        semester_mark_sheets = [
            c for c in context.credentials
            if c.document_type == DocumentType.SEMESTER_MARK_SHEET
            and c.semester_number is not None
            and c.academic_level == AcademicLevel.BACHELOR
        ]

        # Collect found semester numbers
        found_semesters = [c.semester_number for c in semester_mark_sheets if c.semester_number]

        # Create validation result
        validation = BachelorValidation.create(
            expected_semesters=expected_semesters,
            found_semesters=found_semesters,
        )

        # Store validation result in context
        context.set_stage_result(self.name, {
            "validation_applied": True,
            "has_consolidated_mark_sheet": False,
            "expected_semesters": expected_semesters,
            "found_semesters": validation.semesters_found,
            "missing_semesters": validation.semesters_missing,
            "is_complete": validation.is_complete,
        })

        # Add semester records to bachelor credentials
        for bachelor_cred in bachelor_credentials:
            bachelor_cred.semester_records = [
                SemesterRecord(
                    semester_number=cred.semester_number,
                    grade=cred.final_grade,
                    document_reference=cred.source_file,
                )
                for cred in semester_mark_sheets
                if cred.semester_number
            ]

        # Add flag if incomplete
        if not validation.is_complete:
            context.metadata.add_flag(
                f"INCOMPLETE_SEMESTERS: Missing semesters {validation.semesters_missing}"
            )
            self.logger.warning(
                "Bachelor's degree has missing semesters",
                expected=expected_semesters,
                found=validation.semesters_found,
                missing=validation.semesters_missing,
            )

        self.logger.info(
            "Semester validation completed",
            expected_semesters=expected_semesters,
            found_count=len(validation.semesters_found),
            missing_count=len(validation.semesters_missing),
            is_complete=validation.is_complete,
        )

        return context

    def _get_expected_semesters(self, bachelor_credentials: list) -> int:
        """Determine expected number of semesters from Bachelor's credentials.

        Args:
            bachelor_credentials: List of Bachelor's degree credentials

        Returns:
            Expected number of semesters
        """
        # Try to determine from qualification name
        for cred in bachelor_credentials:
            if cred.qualification_name:
                qual_upper = cred.qualification_name.upper()

                for pattern, semesters in BACHELOR_SEMESTER_MAP.items():
                    if pattern in qual_upper:
                        return semesters

        # Default to settings value
        return self.settings.default_bachelor_semesters


def validate_bachelor_semesters(
    credentials: list,
    expected_semesters: int | None = None,
) -> BachelorValidation:
    """Standalone function to validate Bachelor's semester completeness.

    Args:
        credentials: List of CredentialData objects
        expected_semesters: Expected number of semesters (if known)

    Returns:
        BachelorValidation result
    """
    # Find Bachelor's degree credentials
    bachelor_credentials = [
        c for c in credentials
        if c.academic_level == AcademicLevel.BACHELOR
    ]

    if not bachelor_credentials:
        return BachelorValidation(
            expected_semesters=expected_semesters or 8,
            semesters_found=[],
            semesters_missing=list(range(1, (expected_semesters or 8) + 1)),
            is_complete=False,
            notes="No Bachelor's degree found",
        )

    # Determine expected semesters
    if expected_semesters is None:
        for cred in bachelor_credentials:
            if cred.qualification_name:
                qual_upper = cred.qualification_name.upper()
                for pattern, semesters in BACHELOR_SEMESTER_MAP.items():
                    if pattern in qual_upper:
                        expected_semesters = semesters
                        break
                if expected_semesters:
                    break

        if expected_semesters is None:
            expected_semesters = BACHELOR_SEMESTER_MAP["DEFAULT"]

    # Check for consolidated mark sheet first
    consolidated_mark_sheets = [
        c for c in credentials
        if c.document_type == DocumentType.CONSOLIDATED_MARK_SHEET
        and c.academic_level == AcademicLevel.BACHELOR
    ]

    if consolidated_mark_sheets:
        return BachelorValidation(
            expected_semesters=expected_semesters,
            semesters_found=list(range(1, expected_semesters + 1)),
            semesters_missing=[],
            is_complete=True,
            has_consolidated_mark_sheet=True,
            notes="Complete via consolidated mark sheet",
        )

    # Check for transcripts with final grades at Bachelor level
    # International transcripts with complete academic records
    # should be treated as equivalent to consolidated mark sheets
    transcripts_with_grades = [
        c for c in credentials
        if c.document_type == DocumentType.TRANSCRIPT
        and c.academic_level == AcademicLevel.BACHELOR
        and c.final_grade is not None
    ]

    if transcripts_with_grades:
        return BachelorValidation(
            expected_semesters=expected_semesters,
            semesters_found=list(range(1, expected_semesters + 1)),
            semesters_missing=[],
            is_complete=True,
            has_consolidated_mark_sheet=False,
            notes="Complete via transcript with final grade",
        )

    # Find semester mark sheets for Bachelor's level only
    semester_mark_sheets = [
        c for c in credentials
        if c.document_type == DocumentType.SEMESTER_MARK_SHEET
        and c.semester_number is not None
        and c.academic_level == AcademicLevel.BACHELOR
    ]

    found_semesters = [c.semester_number for c in semester_mark_sheets]

    return BachelorValidation.create(
        expected_semesters=expected_semesters,
        found_semesters=found_semesters,
    )
