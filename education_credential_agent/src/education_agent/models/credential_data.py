"""Credential data extraction models."""

from pydantic import BaseModel, Field

from ..config.constants import AcademicLevel, DocumentType, GradingSystem


class Institution(BaseModel):
    """Educational institution information."""

    name: str = Field(..., description="Institution name")
    country: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Country code (ISO 3166-1 alpha-2)",
    )
    city: str | None = Field(default=None, description="City where institution is located")
    state: str | None = Field(default=None, description="State or province")


class GradeInfo(BaseModel):
    """Grade information with conversion details."""

    original_value: str = Field(..., description="Original grade as displayed on document")
    numeric_value: float | None = Field(
        default=None,
        description="Numeric representation of the grade",
    )
    grading_system: GradingSystem = Field(
        default=GradingSystem.OTHER,
        description="Detected grading system",
    )
    french_scale_equivalent: float | None = Field(
        default=None,
        ge=0,
        le=20,
        description="Converted grade on French 0-20 scale",
    )
    max_possible: float | None = Field(
        default=None,
        description="Maximum possible grade in the original system",
    )
    conversion_notes: str | None = Field(
        default=None,
        description="Notes about the conversion process",
    )

    @property
    def is_converted(self) -> bool:
        """Check if grade has been converted to French scale."""
        return self.french_scale_equivalent is not None


class SemesterRecord(BaseModel):
    """Record of a single semester."""

    semester_number: int = Field(..., ge=1, description="Semester number")
    year: str | None = Field(default=None, description="Academic year (e.g., '2020-2021')")
    grade: GradeInfo | None = Field(default=None, description="Semester grade")
    credits: float | None = Field(default=None, description="Credits earned")
    document_reference: str | None = Field(
        default=None,
        description="Reference to the source document",
    )


class BachelorValidation(BaseModel):
    """Validation result for Bachelor's degree semesters."""

    expected_semesters: int = Field(..., ge=1, description="Expected number of semesters")
    semesters_found: list[int] = Field(
        default_factory=list,
        description="List of semester numbers found",
    )
    semesters_missing: list[int] = Field(
        default_factory=list,
        description="List of missing semester numbers",
    )
    is_complete: bool = Field(default=False, description="Whether all semesters are present")
    has_consolidated_mark_sheet: bool = Field(
        default=False,
        description="Whether a consolidated mark sheet was found",
    )
    notes: str | None = Field(default=None, description="Additional validation notes")

    @classmethod
    def create(
        cls,
        expected_semesters: int,
        found_semesters: list[int],
        has_consolidated_mark_sheet: bool = False,
    ) -> "BachelorValidation":
        """Create a validation result from found semesters.

        Args:
            expected_semesters: Expected number of semesters
            found_semesters: List of found semester numbers
            has_consolidated_mark_sheet: Whether a consolidated mark sheet was found

        Returns:
            BachelorValidation instance
        """
        expected = set(range(1, expected_semesters + 1))
        found = set(found_semesters)
        missing = sorted(expected - found)

        return cls(
            expected_semesters=expected_semesters,
            semesters_found=sorted(found_semesters),
            semesters_missing=missing,
            is_complete=len(missing) == 0 or has_consolidated_mark_sheet,
            has_consolidated_mark_sheet=has_consolidated_mark_sheet,
        )


class CredentialData(BaseModel):
    """Extracted credential data from a document."""

    # Source document info
    source_file: str = Field(..., description="Source file path")
    document_type: DocumentType = Field(
        default=DocumentType.UNKNOWN,
        description="Type of document",
    )

    # Academic level
    academic_level: AcademicLevel = Field(
        default=AcademicLevel.OTHER,
        description="Academic level of the qualification",
    )
    qualification_name: str | None = Field(
        default=None,
        description="Name of the qualification (e.g., 'Bachelor of Technology')",
    )
    specialization: str | None = Field(
        default=None,
        description="Specialization or major",
    )

    # Institution
    institution: Institution | None = Field(default=None, description="Institution information")

    # Student info
    student_name: str | None = Field(default=None, description="Student name")
    student_id: str | None = Field(default=None, description="Student ID or roll number")

    # Dates
    issue_date: str | None = Field(default=None, description="Document issue date")
    completion_date: str | None = Field(default=None, description="Completion date")
    year_of_passing: str | None = Field(default=None, description="Year of passing")

    # Grades
    final_grade: GradeInfo | None = Field(default=None, description="Final/overall grade")
    semester_number: int | None = Field(
        default=None,
        ge=1,
        description="Semester number (for semester mark sheets)",
    )
    semester_records: list[SemesterRecord] = Field(
        default_factory=list,
        description="Individual semester records",
    )

    # Status
    is_provisional: bool = Field(
        default=False,
        description="Whether this is a provisional certificate",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in extracted data",
    )

    # Raw data
    raw_extracted_text: str | None = Field(
        default=None,
        description="Raw OCR text (for debugging)",
    )

    @property
    def country(self) -> str | None:
        """Get the country code from institution."""
        return self.institution.country if self.institution else None

    @property
    def is_bachelor(self) -> bool:
        """Check if this is a Bachelor's degree credential."""
        return self.academic_level == AcademicLevel.BACHELOR

    @property
    def is_semester_mark_sheet(self) -> bool:
        """Check if this is a semester mark sheet."""
        return self.document_type == DocumentType.SEMESTER_MARK_SHEET
