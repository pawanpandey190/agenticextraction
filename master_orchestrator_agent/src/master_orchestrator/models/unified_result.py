"""Unified result models for Master Orchestrator Agent."""

from datetime import date
from typing import Any
from pydantic import BaseModel, Field

from master_orchestrator.config.constants import ValidationStatus, WorthinessStatus


class MRZDetails(BaseModel):
    """MRZ data extracted from passport."""

    document_type: str | None = None
    raw_line1: str | None = None
    raw_line2: str | None = None
    checksum_valid: bool | None = None


class PassportDetails(BaseModel):
    """Normalized passport data from passport agent."""

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None  # ISO format YYYY-MM-DD
    sex: str | None = None  # M, F, or X
    passport_number: str | None = None
    issuing_country: str | None = None  # 3-letter ICAO code
    issue_date: str | None = None  # ISO format YYYY-MM-DD
    expiry_date: str | None = None  # ISO format YYYY-MM-DD
    mrz_data: MRZDetails | None = None
    accuracy_score: int = 0  # 0-100

    # Extraction status
    extraction_status: str = "success"  # success, partial, failed
    failure_reason: str | None = None

    @property
    def full_name(self) -> str | None:
        """Get full name from first and last name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name


class EducationSummary(BaseModel):
    """Normalized education data from education agent."""

    highest_qualification: str | None = None
    institution: str | None = None
    country: str | None = None  # ISO 3166-1 alpha-2
    student_name: str | None = None
    final_grade_original: str | None = None
    french_equivalent_grade_0_20: float | None = None
    validation_status: ValidationStatus = ValidationStatus.INCONCLUSIVE
    remarks: str = ""

    # Extraction status
    extraction_status: str = "success"  # success, partial, failed
    failure_reason: str | None = None


class FinancialSummary(BaseModel):
    """Normalized financial data from financial agent."""

    document_type: str | None = None  # BANK_STATEMENT, BANK_LETTER, CERTIFICATE
    account_holder_name: str | None = None
    bank_name: str | None = None
    base_currency: str | None = None  # ISO 4217 code
    amount_original: float | None = None
    amount_eur: float | None = None
    financial_threshold_eur: float = 15000.0
    worthiness_status: WorthinessStatus = WorthinessStatus.INCONCLUSIVE
    remarks: str = ""

    # Extraction status
    extraction_status: str = "success"  # success, partial, failed
    failure_reason: str | None = None


class CrossValidation(BaseModel):
    """Cross-validation results across documents."""

    name_match: bool | None = None
    name_match_score: float | None = None  # Fuzzy match score
    dob_match: bool | None = None
    remarks: str = ""

    # Details for debugging
    passport_name: str | None = None
    education_name: str | None = None
    financial_name: str | None = None
    passport_dob: str | None = None
    education_dob: str | None = None


class ProcessingMetadata(BaseModel):
    """Metadata about the processing run."""

    total_documents_scanned: int = 0
    documents_by_category: dict[str, int] = Field(default_factory=dict)
    processing_errors: list[str] = Field(default_factory=list)
    processing_warnings: list[str] = Field(default_factory=list)
    processing_time_seconds: float | None = None


class MasterAnalysisResult(BaseModel):
    """Complete unified result from master orchestrator."""

    passport_details: PassportDetails | None = None
    education_summary: EducationSummary | None = None
    financial_summary: FinancialSummary | None = None
    cross_validation: CrossValidation | None = None
    metadata: ProcessingMetadata = Field(default_factory=ProcessingMetadata)

    def to_output_dict(self) -> dict[str, Any]:
        """Convert to output dictionary matching final_output.md schema."""
        result: dict[str, Any] = {}

        if self.passport_details:
            result["passport_details"] = {
                "first_name": self.passport_details.first_name or "",
                "last_name": self.passport_details.last_name or "",
                "date_of_birth": self.passport_details.date_of_birth or "",
                "sex": self.passport_details.sex or "",
                "passport_number": self.passport_details.passport_number or "",
                "issuing_country": self.passport_details.issuing_country or "",
                "issue_date": self.passport_details.issue_date or "",
                "expiry_date": self.passport_details.expiry_date or "",
                "mrz_data": (
                    self.passport_details.mrz_data.model_dump()
                    if self.passport_details.mrz_data
                    else {}
                ),
                "accuracy_score": self.passport_details.accuracy_score,
            }

        if self.education_summary:
            result["education_summary"] = {
                "highest_qualification": self.education_summary.highest_qualification or "",
                "institution": self.education_summary.institution or "",
                "country": self.education_summary.country or "",
                "final_grade_original": self.education_summary.final_grade_original or "",
                "french_equivalent_grade_0_20": self.education_summary.french_equivalent_grade_0_20,
                "validation_status": self.education_summary.validation_status.value,
                "remarks": self.education_summary.remarks,
            }

        if self.financial_summary:
            result["financial_summary"] = {
                "document_type": self.financial_summary.document_type or "",
                "base_currency": self.financial_summary.base_currency or "",
                "amount_original": self.financial_summary.amount_original or 0,
                "amount_eur": self.financial_summary.amount_eur or 0,
                "financial_threshold_eur": self.financial_summary.financial_threshold_eur,
                "worthiness_status": self.financial_summary.worthiness_status.value,
                "remarks": self.financial_summary.remarks,
            }

        if self.cross_validation:
            result["cross_validation"] = {
                "name_match": self.cross_validation.name_match,
                "dob_match": self.cross_validation.dob_match,
                "remarks": self.cross_validation.remarks,
            }

        return result
