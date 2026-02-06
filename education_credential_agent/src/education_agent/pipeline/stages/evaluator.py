"""Final evaluation stage for generating the output JSON."""

from pathlib import Path

from ...config.constants import AcademicLevel, DocumentType, SemesterValidationStatus
from ...config.settings import Settings
from ...models.evaluation import (
    AnalysisResult,
    DocumentAnalyzed,
    EvaluationResult,
    GradeConversionResult,
    HighestQualification,
    SemesterValidationResult,
)
from ..base import PipelineContext, PipelineStage


class EvaluatorStage(PipelineStage):
    """Stage for final evaluation and JSON output generation."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    @property
    def name(self) -> str:
        return "evaluator"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Generate final evaluation result.

        Args:
            context: Pipeline context

        Returns:
            Updated context with analysis result
        """
        # Build list of analyzed documents
        documents_analyzed = []
        for credential in context.credentials:
            doc = DocumentAnalyzed(
                file_name=Path(credential.source_file).name,
                document_type=credential.document_type,
                country=credential.country,
                institution=credential.institution.name if credential.institution else None,
                qualification=credential.qualification_name,
                grading_system=credential.final_grade.grading_system if credential.final_grade else None,
                academic_level=credential.academic_level,
                semester_number=credential.semester_number,
                confidence=credential.confidence_score,
            )
            documents_analyzed.append(doc)

        # Determine highest qualification
        highest_qualification = self._find_highest_qualification(context.credentials)

        # Build evaluation result
        evaluation = self._build_evaluation_result(context)

        # Build final analysis result
        analysis_result = AnalysisResult(
            documents_analyzed=documents_analyzed,
            highest_qualification=highest_qualification,
            evaluation=evaluation,
            flags=context.metadata.flags.copy(),
            errors=context.metadata.errors.copy(),
            processing_summary={
                "total_documents": len(context.documents),
                "credentials_extracted": len(context.credentials),
                "pages_processed": context.metadata.pages_processed,
                "duration_seconds": context.metadata.processing_duration_seconds,
            },
        )

        context.analysis_result = analysis_result

        self.logger.info(
            "Evaluation completed",
            documents_analyzed=len(documents_analyzed),
            highest_level=highest_qualification.level.value if highest_qualification else None,
            flags_count=len(context.metadata.flags),
        )

        context.set_stage_result(self.name, {
            "documents_analyzed": len(documents_analyzed),
            "highest_qualification": highest_qualification.level.value if highest_qualification else None,
        })

        return context

    def _find_highest_qualification(self, credentials: list) -> HighestQualification | None:
        """Find the highest qualification from all credentials.

        Args:
            credentials: List of CredentialData objects

        Returns:
            HighestQualification or None
        """
        # Filter to degree/certificate documents (not transcripts or mark sheets)
        degree_credentials = [
            c for c in credentials
            if c.document_type in (
                DocumentType.DEGREE_CERTIFICATE,
                DocumentType.DIPLOMA,
                DocumentType.PROVISIONAL_CERTIFICATE,
            )
            or c.academic_level.rank > 0  # Has a ranked academic level
        ]

        if not degree_credentials:
            # Fall back to all credentials
            degree_credentials = credentials

        if not degree_credentials:
            return None

        # Sort by academic level rank (descending)
        degree_credentials.sort(key=lambda c: c.academic_level.rank, reverse=True)

        highest = degree_credentials[0]

        status = "Completed"
        if highest.is_provisional:
            status = "Provisional"
        elif highest.document_type == DocumentType.PROVISIONAL_CERTIFICATE:
            status = "Provisional"

        return HighestQualification(
            level=highest.academic_level,
            qualification_name=highest.qualification_name,
            institution=highest.institution.name if highest.institution else None,
            country=highest.country,
            status=status,
        )

    def _build_evaluation_result(self, context: PipelineContext) -> EvaluationResult:
        """Build the evaluation result with validation and conversion info.

        Args:
            context: Pipeline context

        Returns:
            EvaluationResult
        """
        # Check if Bachelor's rules were applied
        semester_validation_result = context.get_stage_result("semester_validator") or {}
        bachelor_rules_applied = semester_validation_result.get("validation_applied", False)

        # Build semester validation result
        if bachelor_rules_applied:
            # Determine the appropriate status
            if semester_validation_result.get("has_consolidated_mark_sheet", False):
                status = SemesterValidationStatus.COMPLETE_VIA_CONSOLIDATED
            elif semester_validation_result.get("is_complete", False):
                status = SemesterValidationStatus.COMPLETE
            else:
                status = SemesterValidationStatus.INCOMPLETE

            semester_validation = SemesterValidationResult(
                status=status,
                expected_semesters=semester_validation_result.get("expected_semesters"),
                found_semesters=semester_validation_result.get("found_semesters", []),
                missing_semesters=semester_validation_result.get("missing_semesters", []),
            )
        else:
            semester_validation = SemesterValidationResult(
                status=SemesterValidationStatus.NOT_APPLICABLE,
            )

        # Build grade conversion result
        grade_conversion = self._build_grade_conversion_result(context)

        return EvaluationResult(
            bachelor_rules_applied=bachelor_rules_applied,
            semester_validation=semester_validation,
            grade_conversion=grade_conversion,
        )

    def _build_grade_conversion_result(self, context: PipelineContext) -> GradeConversionResult:
        """Build the grade conversion result.

        Args:
            context: Pipeline context

        Returns:
            GradeConversionResult
        """
        # Find the highest credential with a converted grade
        for credential in sorted(
            context.credentials,
            key=lambda c: c.academic_level.rank,
            reverse=True,
        ):
            if not credential.final_grade:
                continue

            french_equivalent = credential.final_grade.french_scale_equivalent
            conversion_possible = french_equivalent is not None

            # For incomplete Bachelor's, don't report final grade (for Indian institutions only)
            # International institutions typically don't have semester-by-semester mark sheets
            semester_result = context.get_stage_result("semester_validator") or {}
            is_incomplete_bachelor = (
                credential.academic_level == AcademicLevel.BACHELOR
                and semester_result.get("validation_applied", False)
                and not semester_result.get("is_complete", True)
            )

            # Only block grade conversion for Indian institutions
            # Non-Indian countries don't typically have semester-by-semester validation
            is_indian_institution = credential.country == "IN"

            if is_incomplete_bachelor and is_indian_institution:
                return GradeConversionResult(
                    conversion_source="GRADE CONVERSION TABLES BY REGION",
                    original_grade=credential.final_grade.original_value,
                    original_scale=credential.final_grade.grading_system,
                    french_equivalent_0_20=None,
                    conversion_notes="Grade not computed - incomplete semester records",
                    conversion_possible=False,
                )

            # For non-Indian institutions with incomplete semester records,
            # still compute the grade but add a note about the validation status
            conversion_notes = credential.final_grade.conversion_notes
            if is_incomplete_bachelor and not is_indian_institution:
                notes = credential.final_grade.conversion_notes or ""
                if notes:
                    notes += "; "
                notes += "Note: Semester validation not applicable for international institutions"
                conversion_notes = notes

            return GradeConversionResult(
                conversion_source="GRADE CONVERSION TABLES BY REGION",
                original_grade=credential.final_grade.original_value,
                original_scale=credential.final_grade.grading_system,
                french_equivalent_0_20=(
                    f"{french_equivalent:.1f}" if french_equivalent is not None else None
                ),
                conversion_notes=conversion_notes,
                conversion_possible=conversion_possible,
            )

        # No grades found
        return GradeConversionResult(
            conversion_source="GRADE CONVERSION TABLES BY REGION",
            conversion_notes="No grades found in documents",
            conversion_possible=False,
        )
