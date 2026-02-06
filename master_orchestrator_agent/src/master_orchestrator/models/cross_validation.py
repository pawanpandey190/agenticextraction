"""Cross-validation models and utilities."""

from pydantic import BaseModel, Field


class NameComparisonResult(BaseModel):
    """Result of comparing names across documents."""

    match: bool
    score: float = Field(ge=0.0, le=1.0)
    source_name: str
    target_name: str
    method: str = "fuzzy"  # fuzzy, exact


class DateComparisonResult(BaseModel):
    """Result of comparing dates across documents."""

    match: bool
    source_date: str | None
    target_date: str | None


class CrossValidationInput(BaseModel):
    """Input data for cross-validation."""

    # From passport
    passport_first_name: str | None = None
    passport_last_name: str | None = None
    passport_dob: str | None = None

    # From education
    education_student_name: str | None = None
    education_dob: str | None = None

    # From financial
    financial_account_holder: str | None = None

    @property
    def passport_full_name(self) -> str | None:
        """Get full name from passport."""
        if self.passport_first_name and self.passport_last_name:
            return f"{self.passport_first_name} {self.passport_last_name}"
        return self.passport_first_name or self.passport_last_name

    @property
    def has_passport_name(self) -> bool:
        """Check if passport name is available."""
        return bool(self.passport_first_name or self.passport_last_name)

    @property
    def has_education_name(self) -> bool:
        """Check if education name is available."""
        return bool(self.education_student_name)

    @property
    def has_financial_name(self) -> bool:
        """Check if financial name is available."""
        return bool(self.financial_account_holder)
