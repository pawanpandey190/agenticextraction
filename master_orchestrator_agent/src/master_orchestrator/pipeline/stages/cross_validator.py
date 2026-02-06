"""Cross Validator Stage - Validates consistency across document types."""

import structlog

from master_orchestrator.models.unified_result import CrossValidation
from master_orchestrator.models.cross_validation import CrossValidationInput
from master_orchestrator.pipeline.base import MasterPipelineContext, MasterPipelineStage
from master_orchestrator.utils.fuzzy_match import fuzzy_match_names, compare_dates

logger = structlog.get_logger(__name__)


class CrossValidatorStage(MasterPipelineStage):
    """Stage 5: Cross-validate data across different document types."""

    @property
    def name(self) -> str:
        return "CrossValidator"

    def process(self, context: MasterPipelineContext) -> MasterPipelineContext:
        """Perform cross-validation between passport, financial, and education data."""
        logger.info("performing_cross_validation")

        # Build input from normalized results
        cv_input = self._build_cross_validation_input(context)

        # Perform validations
        name_match_result = self._validate_names(cv_input, context)
        dob_match_result = self._validate_dob(cv_input, context)

        # Build remarks
        remarks = self._build_remarks(name_match_result, dob_match_result, cv_input)

        context.cross_validation = CrossValidation(
            name_match=name_match_result[0],
            name_match_score=name_match_result[1],
            dob_match=dob_match_result[0],
            remarks=remarks,
            passport_name=cv_input.passport_full_name,
            education_name=cv_input.education_student_name,
            financial_name=cv_input.financial_account_holder,
            passport_dob=cv_input.passport_dob,
            education_dob=cv_input.education_dob,
        )

        logger.info(
            "cross_validation_complete",
            name_match=name_match_result[0],
            name_score=name_match_result[1],
            dob_match=dob_match_result[0],
        )

        return context

    def _build_cross_validation_input(
        self, context: MasterPipelineContext
    ) -> CrossValidationInput:
        """Build cross-validation input from context."""
        cv_input = CrossValidationInput()

        # Extract from passport
        if context.passport_details:
            cv_input.passport_first_name = context.passport_details.first_name
            cv_input.passport_last_name = context.passport_details.last_name
            cv_input.passport_dob = context.passport_details.date_of_birth

        # Extract from education
        if context.education_summary:
            cv_input.education_student_name = context.education_summary.student_name
            # Education agent may not provide DOB directly

        # Extract from financial
        if context.financial_summary:
            cv_input.financial_account_holder = context.financial_summary.account_holder_name

        return cv_input

    def _validate_names(
        self,
        cv_input: CrossValidationInput,
        context: MasterPipelineContext,
    ) -> tuple[bool | None, float | None]:
        """Validate name consistency across documents.

        Returns:
            Tuple of (is_match, score) where None means unable to validate
        """
        threshold = context.settings.name_match_threshold
        passport_name = cv_input.passport_full_name

        if not passport_name:
            logger.debug("no_passport_name_for_validation")
            return None, None

        matches: list[tuple[bool, float]] = []

        # Compare with financial account holder
        if cv_input.financial_account_holder:
            is_match, score = fuzzy_match_names(
                passport_name,
                cv_input.financial_account_holder,
                threshold=threshold,
            )
            matches.append((is_match, score))
            logger.debug(
                "name_comparison_financial",
                passport=passport_name,
                financial=cv_input.financial_account_holder,
                match=is_match,
                score=score,
            )

        # Compare with education student name
        if cv_input.education_student_name:
            is_match, score = fuzzy_match_names(
                passport_name,
                cv_input.education_student_name,
                threshold=threshold,
            )
            matches.append((is_match, score))
            logger.debug(
                "name_comparison_education",
                passport=passport_name,
                education=cv_input.education_student_name,
                match=is_match,
                score=score,
            )

        if not matches:
            # No other names to compare against
            return None, None

        # All comparisons must match
        all_match = all(m[0] for m in matches)
        avg_score = sum(m[1] for m in matches) / len(matches)

        return all_match, avg_score

    def _validate_dob(
        self,
        cv_input: CrossValidationInput,
        context: MasterPipelineContext,
    ) -> tuple[bool | None, str | None, str | None]:
        """Validate date of birth consistency.

        Returns:
            Tuple of (is_match, passport_dob, education_dob)
        """
        passport_dob = cv_input.passport_dob
        education_dob = cv_input.education_dob

        if not passport_dob:
            logger.debug("no_passport_dob_for_validation")
            return None, None, None

        if not education_dob:
            logger.debug("no_education_dob_for_validation")
            return None, passport_dob, None

        is_match, date1_str, date2_str = compare_dates(passport_dob, education_dob)

        logger.debug(
            "dob_comparison",
            passport_dob=date1_str,
            education_dob=date2_str,
            match=is_match,
        )

        return is_match, date1_str, date2_str

    def _build_remarks(
        self,
        name_result: tuple[bool | None, float | None],
        dob_result: tuple[bool | None, str | None, str | None],
        cv_input: CrossValidationInput,
    ) -> str:
        """Build human-readable remarks about validation results."""
        remarks_parts: list[str] = []

        name_match, name_score = name_result
        dob_match = dob_result[0]

        # Name validation remarks
        if name_match is None:
            if not cv_input.passport_full_name:
                remarks_parts.append("Unable to validate names: passport name not extracted")
            else:
                remarks_parts.append(
                    "Unable to validate names: no other document names available"
                )
        elif name_match:
            remarks_parts.append(f"Name match confirmed (score: {name_score:.2f})")
        else:
            remarks_parts.append(
                f"Name mismatch detected (score: {name_score:.2f}). "
                f"Passport: '{cv_input.passport_full_name}', "
                f"Financial: '{cv_input.financial_account_holder or 'N/A'}', "
                f"Education: '{cv_input.education_student_name or 'N/A'}'"
            )

        # DOB validation remarks
        if dob_match is None:
            if not cv_input.passport_dob:
                remarks_parts.append("Unable to validate DOB: passport DOB not extracted")
            else:
                remarks_parts.append("Unable to validate DOB: education DOB not available")
        elif dob_match:
            remarks_parts.append("Date of birth match confirmed")
        else:
            remarks_parts.append(
                f"Date of birth mismatch: passport '{cv_input.passport_dob}' vs "
                f"education '{cv_input.education_dob}'"
            )

        return "; ".join(remarks_parts)
