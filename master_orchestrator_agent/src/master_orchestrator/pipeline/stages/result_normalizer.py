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
            # Diagnostic logging
            logger.info("normalizing_passport_raw_result", 
                         type=type(raw_result).__name__)

            # Access attributes from PassportAnalysisResult
            # Use getattr with a default for the attribute NOT existing, 
            # and 'or' for the attribute existing but being None.
            visual_data = getattr(raw_result, "extracted_passport_data", None)
            mrz_data = getattr(raw_result, "extracted_mrz_data", None)
            accuracy_score = getattr(raw_result, "accuracy_score", 0)
            if accuracy_score is None: accuracy_score = 0
            
            confidence_level = getattr(raw_result, "confidence_level", "LOW")
            if confidence_level is None: confidence_level = "LOW"
            
            remarks = getattr(raw_result, "remarks", "")
            if remarks is None: remarks = ""

            # If it's a dict (fallback)
            if isinstance(raw_result, dict):
                accuracy_score = raw_result.get("accuracy_score") if raw_result.get("accuracy_score") is not None else accuracy_score
                confidence_level = raw_result.get("confidence_level") if raw_result.get("confidence_level") is not None else confidence_level
                remarks = raw_result.get("remarks") if raw_result.get("remarks") is not None else remarks
                visual_data = raw_result.get("extracted_passport_data", visual_data)
                mrz_data = raw_result.get("extracted_mrz_data", mrz_data)

            # Extra check: if remarks is still empty but we have processing errors
            if not remarks and hasattr(raw_result, "processing_errors"):
                errors = getattr(raw_result, "processing_errors", [])
                if errors:
                    remarks = f"Processing attempted but failed with errors: {', '.join(errors)}"

            # Extract MRZ details if available
            mrz_details = None
            if mrz_data is not None:
                # Dict fallback for mrz_data
                if isinstance(mrz_data, dict):
                    raw_line1 = mrz_data.get("raw_line1")
                    raw_line2 = mrz_data.get("raw_line2")
                    doc_type = mrz_data.get("document_type")
                    checksums = mrz_data.get("checksum_results")
                    checksum_valid = None
                    if checksums and isinstance(checksums, dict):
                        checksum_valid = checksums.get("composite")
                else:
                    raw_line1 = getattr(mrz_data, "raw_line1", None)
                    raw_line2 = getattr(mrz_data, "raw_line2", None)
                    doc_type = getattr(mrz_data, "document_type", None)
                    checksum_results = getattr(mrz_data, "checksum_results", None)
                    checksum_valid = None
                    if checksum_results:
                        checksum_valid = getattr(checksum_results, "composite", None)

                mrz_details = MRZDetails(
                    document_type=doc_type,
                    raw_line1=raw_line1,
                    raw_line2=raw_line2,
                    checksum_valid=checksum_valid,
                )

            # Extract visual data
            if visual_data:
                # Dict fallback for visual_data
                if isinstance(visual_data, dict):
                    first_name = visual_data.get("first_name")
                    last_name = visual_data.get("last_name")
                    dob = visual_data.get("date_of_birth")
                    sex = visual_data.get("sex")
                    p_num = visual_data.get("passport_number")
                    country = visual_data.get("issuing_country")
                    i_date = visual_data.get("passport_issue_date")
                    e_date = visual_data.get("passport_expiry_date")
                else:
                    first_name = getattr(visual_data, "first_name", None)
                    last_name = getattr(visual_data, "last_name", None)
                    dob = getattr(visual_data, "date_of_birth", None)
                    sex = getattr(visual_data, "sex", None)
                    p_num = getattr(visual_data, "passport_number", None)
                    country = getattr(visual_data, "issuing_country", None)
                    i_date = getattr(visual_data, "passport_issue_date", None)
                    e_date = getattr(visual_data, "passport_expiry_date", None)

                # Reconcile names using MRZ as a structural guide
                if mrz_data:
                    first_name, last_name = self._reconcile_names(
                        first_name, last_name, mrz_data
                    )

                return PassportDetails(
                    first_name=first_name,
                    last_name=last_name,
                    date_of_birth=dob.isoformat() if hasattr(dob, "isoformat") else str(dob) if dob else None,
                    sex=sex,
                    passport_number=p_num,
                    issuing_country=country,
                    issue_date=i_date.isoformat() if hasattr(i_date, "isoformat") else str(i_date) if i_date else None,
                    expiry_date=e_date.isoformat() if hasattr(e_date, "isoformat") else str(e_date) if e_date else None,
                    mrz_data=mrz_details,
                    accuracy_score=accuracy_score,
                    confidence_level=confidence_level,
                    remarks=remarks,
                    french_equivalence="Authenticité Validée" if accuracy_score >= 70 and confidence_level == "HIGH" else "Authenticité Partielle" if accuracy_score >= 50 else "Authenticité Non Confirmée",
                    extraction_status="success",
                )

            return PassportDetails(
                extraction_status="partial",
                failure_reason="No visual data extracted",
                accuracy_score=accuracy_score,
                confidence_level=confidence_level,
                mrz_data=mrz_details,
                remarks=remarks or "Passport detection partially failed. Visual zone data missing.",
                french_equivalence="Authenticité Non Confirmée",
            )

        except Exception as e:
            logger.error("passport_normalization_error", error=str(e))
            context.add_error(f"Failed to normalize passport result: {str(e)}")
            return PassportDetails(
                extraction_status="failed",
                failure_reason=str(e),
                remarks=f"Normalization error: {str(e)}",
                french_equivalence="Erreur de Validation",
            )

    def _reconcile_names(
        self,
        visual_first: str | None,
        visual_last: str | None,
        mrz_data: object,
    ) -> tuple[str | None, str | None]:
        """Reconcile names between VIZ and MRZ data.
        
        Prioritizes MRZ for structure and VIZ for full (non-truncated) strings.
        """
        try:
            # Extract MRZ names
            if isinstance(mrz_data, dict):
                mrz_first = mrz_data.get("first_name")
                mrz_last = mrz_data.get("last_name")
            else:
                mrz_first = getattr(mrz_data, "first_name", None)
                mrz_last = getattr(mrz_data, "last_name", None)

            if not mrz_first and not mrz_last:
                return visual_first, visual_last

            # If visual is missing, use MRZ
            if not visual_first and not visual_last:
                return mrz_first, mrz_last

            # Normalize for comparison
            v_f = (visual_first or "").upper().strip()
            v_l = (visual_last or "").upper().strip()
            m_f = (mrz_first or "").upper().strip()
            m_l = (mrz_last or "").upper().strip()

            # Extract MRZ metadata for better noise detection
            if isinstance(mrz_data, dict):
                mrz_country = mrz_data.get("issuing_country")
                doc_type = mrz_data.get("document_type")
            else:
                mrz_country = getattr(mrz_data, "issuing_country", None)
                doc_type = getattr(mrz_data, "document_type", None)

            # 1. Noise Removal (Handling cases like P<ETHADUGNA or PRETHADUGNA)
            # If MRZ last name is at the end of visual last name
            m_l_clean = m_l.replace(" ", "")
            v_l_clean = v_l.replace(" ", "")
            if m_l_clean and v_l_clean.endswith(m_l_clean) and v_l_clean != m_l_clean:
                # Check if the prefix contains MRZ markers
                prefix = v_l_clean[:v_l_clean.find(m_l_clean)]
                is_noisy = False
                if mrz_country and mrz_country in prefix: is_noisy = True
                if doc_type and doc_type in prefix: is_noisy = True
                if "<" in prefix or "P<" in visual_last: is_noisy = True
                
                if is_noisy:
                    logger.info("reconciler_stripping_mrz_noise_from_last_name", 
                                 original=visual_last, cleaned=mrz_last)
                    visual_last = mrz_last
                    v_l = m_l

            # 2. Detection of Name Swap
            if v_f == m_l and v_l == m_f:
                logger.info("detected_passport_name_swap_correcting", 
                             visual_first=v_f, visual_last=v_l)
                return visual_last, visual_first

            # 2. Noise Removal (Handling cases like P<ETHADUGNA)
            # If MRZ last name is a sub-part of visual last name (e.g. ADUGNA in PRETHADUGNA)
            if m_l and m_l in v_l and len(m_l) >= 3:
                # If visual is obviously noisy (starts with MRZ boilerplate P<ETH)
                if v_l.startswith("P<") or "ETH" in v_l:
                    visual_last = mrz_last
                    v_l = m_l

            # 3. Handling Truncation
            # If VIZ starts with MRZ or vice versa, they are likely the same name.
            # We prefer VIZ as it contains the full version.
            first_match = (v_f.startswith(m_f) or m_f.startswith(v_f)) if m_f and v_f else False
            last_match = (v_l.startswith(m_l) or m_l.startswith(v_l)) if m_l and v_l else False

            if first_match and last_match:
                return visual_first, visual_last

            # 4. Fundamental Disagreement -> Default to MRZ
            # If they don't share a common prefix, the VIZ is likely hallucinated or misread.
            # However, we only do this if MRZ has a valid name.
            if m_f or m_l:
                logger.info("name_disagreement_defaulting_to_mrz", 
                             visual_first=v_f, visual_last=v_l,
                             mrz_first=m_f, mrz_last=m_l)
                return mrz_first, mrz_last

            return visual_first, visual_last

        except Exception as e:
            logger.warning("name_reconciliation_error", error=str(e))
            return visual_first, visual_last

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
            threshold_eur = context.financial_threshold or context.settings.financial_threshold_eur
            # Build detailed financial remarks
            remarks_parts = []
            
            # Check for generic failure or OCR failure
            if getattr(raw_result, "extraction_status", "success") != "success":
                remarks_parts.append(f"Technical failure during financial data extraction: {getattr(raw_result, 'failure_reason', 'Unknown error')}")
            
            if bank_name:
                remarks_parts.append(f"Financial document from {bank_name} for account holder {account_holder or 'Unknown'}.")
            
            if amount_eur is not None:
                currency_str = f"{original_amount:,.2f} {currency}" if original_amount is not None else "Unknown"
                remarks_parts.append(f"The detected balance is {currency_str}, which converts to approximately {amount_eur:,.2f} EUR.")
                
                if amount_eur >= threshold_eur:
                    remarks_parts.append(f"This exceeds the required threshold of {threshold_eur:,.2f} EUR.")
                else:
                    remarks_parts.append(f"This is below the required threshold of {threshold_eur:,.2f} EUR.")
            elif not remarks_parts:
                remarks_parts.append("Unable to extract balance or account information from the financial document.")
            
            if evaluation and getattr(evaluation, "reason", ""):
                remarks_parts.append(f"Reasoning: {getattr(evaluation, 'reason', '')}")

            remarks = " ".join(remarks_parts)

            if evaluation:
                decision = getattr(evaluation, "decision", None)
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
                french_equivalence="Solvabilité Confirmée" if worthiness_status == WorthinessStatus.PASS else "Insuffisance de Ressources" if worthiness_status == WorthinessStatus.FAIL else "Solvabilité Non Vérifiée",
                extraction_status="success",
            )

        except Exception as e:
            logger.error("financial_normalization_error", error=str(e))
            context.add_error(f"Failed to normalize financial result: {str(e)}")
            return FinancialSummary(
                extraction_status="failed",
                failure_reason=str(e),
                financial_threshold_eur=context.financial_threshold or context.settings.financial_threshold_eur,
                french_equivalence="Erreur de Validation Financière",
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

            # Extract grade conversion info and validation status
            original_grade = None
            french_grade = None
            validation_status = ValidationStatus.INCONCLUSIVE
            
            if evaluation:
                # Grade conversion
                grade_conv = getattr(evaluation, "grade_conversion", None)
                if grade_conv:
                    original_grade = getattr(grade_conv, "original_grade", None)
                    f_grade = getattr(grade_conv, "french_equivalent_0_20", None)
                    if f_grade is not None:
                        try:
                            french_grade = float(f_grade)
                        except (ValueError, TypeError):
                            french_grade = None
                
                # Validation status
                sem_val = getattr(evaluation, "semester_validation", None)
                if sem_val:
                    status = getattr(sem_val, "status", None)
                    if status:
                        status_str = status.value if hasattr(status, "value") else str(status)
                        if status_str == "VALID":
                            validation_status = ValidationStatus.PASS
                        elif status_str == "INVALID":
                            validation_status = ValidationStatus.FAIL

            # Build detailed education remarks
            remarks_parts = []
            
            # Detection of extraction failure
            if getattr(raw_result, "extraction_status", "success") != "success":
                remarks_parts.append(f"TECHNICAL FAILURE: {getattr(raw_result, 'failure_reason', 'Unknown error')}")

            if qualification_name:
                remarks_parts.append(f"Highest qualification: {qualification_name} from {institution or 'Unknown Institution'} ({country or 'Unknown Country'}).")
            
            # Grades
            if original_grade:
                if french_grade is not None:
                    remarks_parts.append(f"Academic Performance: The original grade of {original_grade} was successfully converted to {french_grade:.2f}/20 on the French scale.")
                else:
                    remarks_parts.append(f"Academic Performance: Original grade detected as {original_grade}.")

            # Conversion notes (Why/How conversion was done)
            if evaluation and getattr(evaluation, "grade_conversion", None):
                notes = getattr(evaluation.grade_conversion, "conversion_notes", "")
                if notes and notes != "None":
                    remarks_parts.append(f"Conversion Info: {notes}")

            # Validation Status and "Why"
            if validation_status == ValidationStatus.PASS:
                remarks_parts.append("Validation: PASSED. All required semesters were found and verified.")
            elif validation_status == ValidationStatus.FAIL:
                remarks_parts.append("Validation: FAILED.")
            else:
                remarks_parts.append("Validation: INCONCLUSIVE. The documents provided do not allow for a full semester-by-semester verification.")
            
            # Missing semesters detail
            if evaluation:
                sem_val = getattr(evaluation, "semester_validation", None)
                if sem_val:
                    missing = getattr(sem_val, "missing_semesters", [])
                    if missing:
                        remarks_parts.append(f"Missing semester records: {', '.join(map(str, missing))}. A full set of transcripts is required for a positive evaluation.")
                
            # Add flags/warnings
            flags = getattr(raw_result, "flags", [])
            if flags:
                remarks_parts.append(f"Alerts: {', '.join(flags)}")

            remarks = " ".join(remarks_parts)

            # Try to get student name from raw result first
            student_name = getattr(raw_result, "student_name", None)
            
            # Fallback to passport details if not extracted by education agent
            if not student_name and context.passport_details:
                student_name = context.passport_details.full_name
            
            if not student_name:
                docs_analyzed = getattr(raw_result, "documents_analyzed", [])
                if docs_analyzed:
                    # Fallback or other logic if needed
                    pass

            return EducationSummary(
                highest_qualification=qualification_name,
                institution=institution,
                country=country,
                student_name=student_name,
                final_grade_original=original_grade,
                french_equivalent_grade_0_20=french_grade,
                validation_status=validation_status,
                remarks=remarks,
                french_equivalence="Équivalence Validée" if validation_status == ValidationStatus.PASS else "Équivalence Non Validée" if validation_status == ValidationStatus.FAIL else "Équivalence Partielle",
                extraction_status="success",
            )

        except Exception as e:
            logger.error("education_normalization_error", error=str(e))
            context.add_error(f"Failed to normalize education result: {str(e)}")
            return EducationSummary(
                extraction_status="failed",
                failure_reason=str(e),
            )
