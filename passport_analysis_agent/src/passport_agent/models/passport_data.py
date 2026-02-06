"""Visual passport data models."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class VisualPassportData(BaseModel):
    """Data extracted from the Visual Inspection Zone (VIZ) of a passport.

    This represents the human-readable text on the passport data page,
    extracted using OCR/Vision AI.
    """

    first_name: str | None = Field(
        default=None, description="Given name(s) - uppercase, trimmed"
    )
    last_name: str | None = Field(
        default=None, description="Surname/family name - uppercase, trimmed"
    )
    date_of_birth: date | None = Field(default=None, description="Date of birth")
    passport_number: str | None = Field(
        default=None, description="Passport/document number"
    )
    issuing_country: str | None = Field(
        default=None, description="3-letter ICAO country code"
    )
    nationality: str | None = Field(
        default=None, description="3-letter ICAO nationality code"
    )
    passport_issue_date: date | None = Field(
        default=None, description="Passport issue date"
    )
    passport_expiry_date: date | None = Field(
        default=None, description="Passport expiry date"
    )
    sex: Literal["M", "F", "X"] | None = Field(
        default=None, description="Sex (M=Male, F=Female, X=Unspecified)"
    )
    place_of_birth: str | None = Field(default=None, description="Place of birth")
    ocr_confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="OCR confidence score (0.0-1.0)"
    )

    model_config = {"extra": "forbid"}

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def uppercase_and_strip(cls, v: str | None) -> str | None:
        """Convert names to uppercase and strip whitespace."""
        if v is None:
            return None
        return v.upper().strip()

    @field_validator("passport_number", mode="before")
    @classmethod
    def normalize_passport_number(cls, v: str | None) -> str | None:
        """Normalize passport number."""
        if v is None:
            return None
        # Remove spaces and convert to uppercase
        return v.replace(" ", "").strip().upper()

    @field_validator("issuing_country", "nationality", mode="before")
    @classmethod
    def uppercase_country_code(cls, v: str | None) -> str | None:
        """Convert country codes to uppercase."""
        if v is None:
            return None
        return v.upper().strip()

    @field_validator("sex", mode="before")
    @classmethod
    def normalize_sex(cls, v: str | None) -> str | None:
        """Normalize sex field."""
        if v is None:
            return None
        v = v.upper().strip()
        if v in ("M", "MALE"):
            return "M"
        if v in ("F", "FEMALE"):
            return "F"
        return "X"

    def has_required_fields(self) -> bool:
        """Check if all required fields for validation are present."""
        return all(
            [
                self.first_name,
                self.last_name,
                self.date_of_birth,
                self.passport_number,
            ]
        )


class VisualExtractionResponse(BaseModel):
    """Response model for Claude Vision extraction."""

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None
    passport_number: str | None = None
    issuing_country: str | None = None
    nationality: str | None = None
    passport_issue_date: str | None = None
    passport_expiry_date: str | None = None
    sex: str | None = None
    place_of_birth: str | None = None
    confidence: float = 0.0

    model_config = {"extra": "ignore"}
