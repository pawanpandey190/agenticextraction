"""Result Normalizer Stage - Transforms sub-agent results to unified format."""

import structlog

from master_orchestrator.config.constants import ValidationStatus, WorthinessStatus
from master_orchestrator.models.unified_result import (
    PassportDetails,
    EducationSummary,
    FinancialSummary,
    MRZDetails,
)
from master_orchestrator.pipeline.base import MasterPipelineContext, MasterPipelineStage

logger = structlog.get_logger(__name__)


class ResultNormalizerStage(MasterPipelineStage):
    """Stage 4: Normalize sub-agent results to unified format."""

    @property
    def name(self) -> str:
        return "ResultNormalizer"

    def process(self, context: MasterPipelineContext) -> MasterPipelineContext:
        """Transform all sub-agent results to unified format."""
        logger.info("normalizing_results")

        # Normalize passport result
        if context.passport_raw_result is not None:
            context.passport_details = self._normalize_passport(
                context.passport_raw_result, context
            )

        # Normalize financial result
        if context.financial_raw_result is not None:
            context.financial_summary = self._normalize_financial(
                context.financial_raw_result, context
            )

        # Normalize education result
        if context.education_raw_result is not None:
            context.education_summary = self._normalize_education(
                context.education_raw_result, context
            )

        logger.info(
            "normalization_complete",
            passport=context.passport_details is not None,
            financial=context.financial_summary is not None,
            education=context.education_summary is not None,
        )

        return context

    def _normalize_passport(
        self,
        raw_result: object,
        context: MasterPipelineContext,
    ) -> PassportDetails:
        """Normalize passport agent result to PassportDetails."""
        try:
            # Access attributes from PassportAnalysisResult
            visual_data = getattr(raw_result, "extracted_passport_data", None)
            mrz_data = getattr(raw_result, "extracted_mrz_data", None)
            accuracy_score = getattr(raw_result, "accuracy_score", 0)

            # Extract MRZ details if available
            mrz_details = None
            if mrz_data is not None:
                checksum_results = getattr(mrz_data, "checksum_results", None)
                checksum_valid = None
                if checksum_results:
                    checksum_valid = getattr(checksum_results, "composite_valid", None)

                mrz_details = MRZDetails(
                    document_type=getattr(mrz_data, "document_type", None),
                    raw_line1=getattr(mrz_data, "raw_line1", None),
                    raw_line2=getattr(mrz_data, "raw_line2", None),
                    checksum_valid=checksum_valid,
                )

            # Extract visual data
            if visual_data:
                dob = getattr(visual_data, "date_of_birth", None)
                issue_date = getattr(visual_data, "passport_issue_date", None)
                expiry_date = getattr(visual_data, "passport_expiry_date", None)

                return PassportDetails(
                    first_name=getattr(visual_data, "first_name", None),
                    last_name=getattr(visual_data, "last_name", None),
                    date_of_birth=dob.isoformat() if dob else None,
                    sex=getattr(visual_data, "sex", None),
                    passport_number=getattr(visual_data, "passport_number", None),
                    issuing_country=getattr(visual_data, "issuing_country", None),
                    issue_date=issue_date.isoformat() if issue_date else None,
                    expiry_date=expiry_date.isoformat() if expiry_date else None,
                    mrz_data=mrz_details,
                    accuracy_score=accuracy_score,
                    extraction_status="success",
                )

            return PassportDetails(
                extraction_status="partial",
                failure_reason="No visual data extracted",
                accuracy_score=accuracy_score,
                mrz_data=mrz_details,
            )

        except Exception as e:
            logger.error("passport_normalization_error", error=str(e))
            context.add_error(f"Failed to normalize passport result: {str(e)}")
            return PassportDetails(
                extraction_status="failed",
                failure_reason=str(e),
            )

    def _normalize_financial(
        self,
        raw_result: object,
        context: MasterPipelineContext,
    ) -> FinancialSummary:
        """Normalize financial agent result to FinancialSummary."""
        try:
            # Access attributes from AnalysisResult
            doc_type = getattr(raw_result, "document_type", None)
            account_holder = getattr(raw_result, "account_holder", None)
            bank_name = getattr(raw_result, "bank_name", None)
            currency = getattr(raw_result, "currency_detected", None)

            # Get converted amount
            converted = getattr(raw_result, "converted_to_eur", None)
            amount_eur = None
            original_amount = None
            if converted:
                amount_eur = getattr(converted, "amount_eur", None)
                original_amount = getattr(converted, "original_amount", None)

            # Get evaluation result
            evaluation = getattr(raw_result, "financial_worthiness", None)
            worthiness_status = WorthinessStatus.INCONCLUSIVE
            threshold_eur = context.settings.financial_threshold_eur
            remarks = ""

            if evaluation:
                decision = getattr(evaluation, "decision", None)
                threshold_eur = getattr(evaluation, "threshold_eur", threshold_eur)
                remarks = getattr(evaluation, "reason", "")

                if decision:
                    decision_value = (
                        decision.value if hasattr(decision, "value") else str(decision)
                    )
                    if decision_value == "WORTHY":
                        worthiness_status = WorthinessStatus.PASS
                    elif decision_value == "NOT_WORTHY":
                        worthiness_status = WorthinessStatus.FAIL
                    else:
                        worthiness_status = WorthinessStatus.INCONCLUSIVE

            # Get document type value
            doc_type_str = None
            if doc_type:
                doc_type_str = doc_type.value if hasattr(doc_type, "value") else str(doc_type)

            return FinancialSummary(
                document_type=doc_type_str,
                account_holder_name=account_holder,
                bank_name=bank_name,
                base_currency=currency,
                amount_original=original_amount,
                amount_eur=amount_eur,
                financial_threshold_eur=threshold_eur,
                worthiness_status=worthiness_status,
                remarks=remarks,
                extraction_status="success",
            )

        except Exception as e:
            logger.error("financial_normalization_error", error=str(e))
            context.add_error(f"Failed to normalize financial result: {str(e)}")
            return FinancialSummary(
                extraction_status="failed",
                failure_reason=str(e),
                financial_threshold_eur=context.settings.financial_threshold_eur,
            )

    def _normalize_education(
        self,
        raw_result: object,
        context: MasterPipelineContext,
    ) -> EducationSummary:
        """Normalize education agent result to EducationSummary."""
        try:
            # Access attributes from AnalysisResult
            highest_qual = getattr(raw_result, "highest_qualification", None)
            evaluation = getattr(raw_result, "evaluation", None)

            # Extract highest qualification info
            qualification_name = None
            institution = None
            country = None

            if highest_qual:
                qualification_name = getattr(highest_qual, "qualification_name", None)
                institution = getattr(highest_qual, "institution", None)
                country = getattr(highest_qual, "country", None)

            # Extract grade conversion info
            original_grade = None
            french_grade = None
            validation_status = ValidationStatus.INCONCLUSIVE
            remarks = ""

            if evaluation:
                grade_conversion = getattr(evaluation, "grade_conversion", None)
                semester_validation = getattr(evaluation, "semester_validation", None)

                if grade_conversion:
                    original_grade = getattr(grade_conversion, "original_grade", None)
                    french_grade_str = getattr(
                        grade_conversion, "french_equivalent_0_20", None
                    )
                    if french_grade_str:
                        try:
                            french_grade = float(french_grade_str)
                        except (ValueError, TypeError):
                            french_grade = None

                    notes = getattr(grade_conversion, "conversion_notes", "")
                    if notes:
                        remarks = notes

                if semester_validation:
                    status = getattr(semester_validation, "status", None)
                    if status:
                        status_value = (
                            status.value if hasattr(status, "value") else str(status)
                        )
                        if status_value == "VALID":
                            validation_status = ValidationStatus.PASS
                        elif status_value == "INVALID":
                            validation_status = ValidationStatus.FAIL
                        else:
                            validation_status = ValidationStatus.INCONCLUSIVE

            # Try to get student name from documents analyzed
            student_name = None
            docs_analyzed = getattr(raw_result, "documents_analyzed", [])
            if docs_analyzed:
                # Student name might be in the first document
                first_doc = docs_analyzed[0] if docs_analyzed else None
                if first_doc:
                    # Try to get student name from credential data
                    pass  # Education agent doesn't expose student name in summary

            return EducationSummary(
                highest_qualification=qualification_name,
                institution=institution,
                country=country,
                student_name=student_name,
                final_grade_original=original_grade,
                french_equivalent_grade_0_20=french_grade,
                validation_status=validation_status,
                remarks=remarks,
                extraction_status="success",
            )

        except Exception as e:
            logger.error("education_normalization_error", error=str(e))
            context.add_error(f"Failed to normalize education result: {str(e)}")
            return EducationSummary(
                extraction_status="failed",
                failure_reason=str(e),
            )
