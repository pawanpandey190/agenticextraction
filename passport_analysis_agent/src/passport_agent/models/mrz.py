"""MRZ (Machine Readable Zone) data models."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MRZChecksumResult(BaseModel):
    """Results of MRZ checksum validation."""

    passport_number: bool = Field(
        default=False, description="Passport number checksum valid"
    )
    date_of_birth: bool = Field(
        default=False, description="Date of birth checksum valid"
    )
    expiry_date: bool = Field(default=False, description="Expiry date checksum valid")
    composite: bool = Field(default=False, description="Composite checksum valid")

    model_config = {"extra": "forbid"}

    @property
    def all_valid(self) -> bool:
        """Check if all checksums are valid."""
        return all(
            [
                self.passport_number,
                self.date_of_birth,
                self.expiry_date,
                self.composite,
            ]
        )

    @property
    def valid_count(self) -> int:
        """Get count of valid checksums."""
        return sum(
            [
                self.passport_number,
                self.date_of_birth,
                self.expiry_date,
                self.composite,
            ]
        )

    def to_dict(self) -> dict[str, bool]:
        """Convert to dictionary for output."""
        return {
            "passport_number": self.passport_number,
            "date_of_birth": self.date_of_birth,
            "expiry_date": self.expiry_date,
            "composite": self.composite,
        }


class MRZData(BaseModel):
    """Parsed MRZ data from TD3 format passport.

    TD3 format has 2 lines of 44 characters each (88 total).
    """

    document_type: str = Field(description="Document type (usually 'P' for passport)")
    issuing_country: str = Field(description="3-letter ICAO issuing country code")
    last_name: str = Field(description="Surname/family name")
    first_name: str = Field(description="Given name(s)")
    passport_number: str = Field(description="Passport/document number")
    nationality: str = Field(description="3-letter ICAO nationality code")
    date_of_birth: date = Field(description="Date of birth")
    sex: Literal["M", "F", "X"] = Field(
        description="Sex (M=Male, F=Female, X=Unspecified)"
    )
    expiry_date: date = Field(description="Passport expiry date")
    personal_number: str | None = Field(
        default=None, description="Personal/national ID number (optional)"
    )
    raw_line1: str = Field(description="Raw MRZ line 1 (44 characters)")
    raw_line2: str = Field(description="Raw MRZ line 2 (44 characters)")
    checksum_results: MRZChecksumResult = Field(
        default_factory=MRZChecksumResult, description="Checksum validation results"
    )

    model_config = {"extra": "forbid"}

    @field_validator("document_type", mode="before")
    @classmethod
    def normalize_document_type(cls, v: str) -> str:
        """Normalize document type."""
        return v.upper().strip()

    @field_validator("issuing_country", "nationality", mode="before")
    @classmethod
    def uppercase_country_code(cls, v: str) -> str:
        """Convert country codes to uppercase."""
        return v.upper().strip().replace("<", "")

    @field_validator("last_name", "first_name", mode="before")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normalize MRZ names."""
        # Replace < with space and strip
        return v.replace("<", " ").strip().upper()

    @field_validator("passport_number", mode="before")
    @classmethod
    def normalize_passport_number(cls, v: str) -> str:
        """Normalize passport number."""
        # Remove filler characters
        return v.replace("<", "").strip().upper()

    @field_validator("sex", mode="before")
    @classmethod
    def normalize_sex(cls, v: str) -> str:
        """Normalize sex field from MRZ."""
        v = v.upper().strip()
        if v == "M":
            return "M"
        if v == "F":
            return "F"
        return "X"  # < or other -> unspecified

    @property
    def full_name(self) -> str:
        """Get full name as single string."""
        return f"{self.first_name} {self.last_name}".strip()


class MRZExtractionResponse(BaseModel):
    """Response model for MRZ extraction from image."""

    line1: str | None = Field(default=None, description="First MRZ line (44 chars)")
    line2: str | None = Field(default=None, description="Second MRZ line (44 chars)")
    confidence: float = Field(default=0.0, description="Extraction confidence")

    model_config = {"extra": "ignore"}

    @property
    def has_valid_lines(self) -> bool:
        """Check if both lines are present and valid length."""
        if not self.line1 or not self.line2:
            return False
        return len(self.line1) == 44 and len(self.line2) == 44
