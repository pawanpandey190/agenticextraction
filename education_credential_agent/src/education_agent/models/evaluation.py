"""Evaluation result models for the final JSON output."""

from pydantic import BaseModel, Field

from ..config.constants import AcademicLevel, DocumentType, GradingSystem, SemesterValidationStatus


class DocumentAnalyzed(BaseModel):
    """Information about a single analyzed document."""

    file_name: str = Field(..., description="Name of the analyzed file")
    document_type: DocumentType = Field(..., description="Type of document")
    country: str | None = Field(default=None, description="Country code (ISO 3166-1 alpha-2)")
    institution: str | None = Field(default=None, description="Institution name")
    qualification: str | None = Field(default=None, description="Qualification name")
    grading_system: GradingSystem | None = Field(default=None, description="Detected grading system")
    academic_level: AcademicLevel | None = Field(default=None, description="Academic level")
    semester_number: int | None = Field(default=None, description="Semester number if applicable")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Extraction confidence")


class HighestQualification(BaseModel):
    """Information about the highest qualification found."""

    level: AcademicLevel = Field(..., description="Academic level")
    qualification_name: str | None = Field(default=None, description="Name of the qualification")
    institution: str | None = Field(default=None, description="Institution name")
    country: str | None = Field(default=None, description="Country code")
    status: str = Field(default="Unknown", description="Status (Completed, Provisional, etc.)")


class SemesterValidationResult(BaseModel):
    """Result of semester validation for Bachelor's degrees."""

    status: SemesterValidationStatus = Field(
        default=SemesterValidationStatus.NOT_APPLICABLE,
        description="Validation status",
    )
    expected_semesters: int | None = Field(
        default=None,
        description="Expected number of semesters",
    )
    found_semesters: list[int] = Field(
        default_factory=list,
        description="List of found semester numbers",
    )
    missing_semesters: list[int] = Field(
        default_factory=list,
        description="List of missing semester numbers",
    )


class GradeConversionResult(BaseModel):
    """Result of grade conversion to French scale."""

    conversion_source: str = Field(
        default="GRADE CONVERSION TABLES BY REGION",
        description="Source used for conversion",
    )
    original_grade: str | None = Field(default=None, description="Original grade value")
    original_scale: GradingSystem | None = Field(default=None, description="Original grading system")
    french_equivalent_0_20: str | None = Field(
        default=None,
        description="French scale equivalent (0-20)",
    )
    conversion_notes: str | None = Field(
        default=None,
        description="Notes about the conversion",
    )
    conversion_possible: bool = Field(
        default=True,
        description="Whether conversion was possible",
    )


class EvaluationResult(BaseModel):
    """Complete evaluation result combining validation and conversion."""

    bachelor_rules_applied: bool = Field(
        default=False,
        description="Whether Bachelor's validation rules were applied",
    )
    semester_validation: SemesterValidationResult = Field(
        default_factory=SemesterValidationResult,
        description="Semester validation result",
    )
    grade_conversion: GradeConversionResult = Field(
        default_factory=GradeConversionResult,
        description="Grade conversion result",
    )


class AnalysisResult(BaseModel):
    """Complete analysis result for all documents (JSON output format)."""

    documents_analyzed: list[DocumentAnalyzed] = Field(
        default_factory=list,
        description="List of all analyzed documents",
    )
    highest_qualification: HighestQualification | None = Field(
        default=None,
        description="Highest qualification found",
    )
    student_name: str | None = Field(default=None, description="Student name extracted from documents")
    evaluation: EvaluationResult = Field(
        default_factory=EvaluationResult,
        description="Evaluation results",
    )
    flags: list[str] = Field(
        default_factory=list,
        description="Processing flags and warnings",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Processing errors",
    )
    processing_summary: dict = Field(
        default_factory=dict,
        description="Summary of processing (documents count, duration, etc.)",
    )
