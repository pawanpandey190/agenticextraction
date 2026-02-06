"""Grade conversion table models."""

from typing import Literal

from pydantic import BaseModel, Field


class GradeRange(BaseModel):
    """A range of grades with French equivalent mapping."""

    min_value: float = Field(..., description="Minimum value in the range (inclusive)")
    max_value: float = Field(..., description="Maximum value in the range (inclusive)")
    french_min: float = Field(..., ge=0, le=20, description="French scale minimum (0-20)")
    french_max: float = Field(..., ge=0, le=20, description="French scale maximum (0-20)")

    def contains(self, value: float) -> bool:
        """Check if a value falls within this range."""
        return self.min_value <= value <= self.max_value

    def convert(self, value: float) -> float:
        """Convert a value to French scale using linear interpolation.

        Args:
            value: The grade value to convert

        Returns:
            French scale equivalent (0-20)
        """
        if not self.contains(value):
            raise ValueError(f"Value {value} not in range [{self.min_value}, {self.max_value}]")

        # Handle edge case where range is a single point
        if self.min_value == self.max_value:
            return (self.french_min + self.french_max) / 2

        # Linear interpolation
        ratio = (value - self.min_value) / (self.max_value - self.min_value)
        return self.french_min + ratio * (self.french_max - self.french_min)


class LetterGradeMapping(BaseModel):
    """Mapping from letter grade to French scale."""

    letter: str = Field(..., description="Letter grade (e.g., 'A', 'B+', 'First')")
    french_min: float = Field(..., ge=0, le=20, description="French scale minimum")
    french_max: float = Field(..., ge=0, le=20, description="French scale maximum")
    description: str | None = Field(default=None, description="Description of the grade")

    def get_french_equivalent(self) -> float:
        """Get the midpoint French equivalent."""
        return (self.french_min + self.french_max) / 2


class CountryGradingSystem(BaseModel):
    """Grading system configuration for a specific country."""

    country_code: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="ISO 3166-1 alpha-2 country code",
    )
    country_name: str = Field(..., description="Full country name")
    system_type: Literal["percentage", "gpa_4", "gpa_10", "letter", "german_5"] = Field(
        ...,
        description="Type of grading system",
    )
    numeric_ranges: list[GradeRange] | None = Field(
        default=None,
        description="Numeric grade ranges for conversion",
    )
    letter_mappings: list[LetterGradeMapping] | None = Field(
        default=None,
        description="Letter grade mappings",
    )
    notes: str | None = Field(
        default=None,
        description="Additional notes about this grading system",
    )

    def convert_numeric(self, value: float) -> float | None:
        """Convert a numeric grade to French scale.

        Args:
            value: The numeric grade value

        Returns:
            French scale equivalent or None if no matching range
        """
        if not self.numeric_ranges:
            return None

        for grade_range in self.numeric_ranges:
            if grade_range.contains(value):
                return grade_range.convert(value)

        return None

    def convert_letter(self, letter: str) -> float | None:
        """Convert a letter grade to French scale.

        Args:
            letter: The letter grade

        Returns:
            French scale equivalent or None if not found
        """
        if not self.letter_mappings:
            return None

        letter_upper = letter.upper().strip()
        for mapping in self.letter_mappings:
            if mapping.letter.upper() == letter_upper:
                return mapping.get_french_equivalent()

        return None


class GradeConversionTable(BaseModel):
    """Complete grade conversion table with country-specific rules."""

    version: str = Field(default="1.0", description="Table version")
    countries: list[CountryGradingSystem] = Field(
        default_factory=list,
        description="Country-specific grading systems",
    )
    default_percentage_ranges: list[GradeRange] = Field(
        default_factory=list,
        description="Default percentage to French scale ranges",
    )
    default_gpa_4_ranges: list[GradeRange] = Field(
        default_factory=list,
        description="Default GPA 4.0 to French scale ranges",
    )
    default_gpa_10_ranges: list[GradeRange] = Field(
        default_factory=list,
        description="Default GPA 10.0 to French scale ranges",
    )

    def get_country_system(self, country_code: str) -> CountryGradingSystem | None:
        """Get the grading system for a specific country.

        Args:
            country_code: ISO 3166-1 alpha-2 country code

        Returns:
            Country grading system or None if not found
        """
        country_code = country_code.upper()
        for country in self.countries:
            if country.country_code.upper() == country_code:
                return country
        return None

    def convert_percentage(self, value: float, country_code: str | None = None) -> float | None:
        """Convert a percentage to French scale.

        Args:
            value: Percentage value (0-100)
            country_code: Optional country code for country-specific conversion

        Returns:
            French scale equivalent or None if conversion not possible
        """
        # Cap percentage at 100
        value = min(value, 100.0)

        # Try country-specific conversion first
        if country_code:
            country_system = self.get_country_system(country_code)
            if country_system and country_system.system_type == "percentage":
                result = country_system.convert_numeric(value)
                if result is not None:
                    return result

        # Fall back to default ranges
        for grade_range in self.default_percentage_ranges:
            if grade_range.contains(value):
                return grade_range.convert(value)

        return None

    def convert_gpa_4(self, value: float, country_code: str | None = None) -> float | None:
        """Convert a 4.0 GPA to French scale.

        Args:
            value: GPA value (0-4.0)
            country_code: Optional country code for country-specific conversion

        Returns:
            French scale equivalent or None if conversion not possible
        """
        # Try country-specific conversion first
        if country_code:
            country_system = self.get_country_system(country_code)
            if country_system and country_system.system_type == "gpa_4":
                result = country_system.convert_numeric(value)
                if result is not None:
                    return result

        # Fall back to default ranges
        for grade_range in self.default_gpa_4_ranges:
            if grade_range.contains(value):
                return grade_range.convert(value)

        return None

    def convert_gpa_10(self, value: float, country_code: str | None = None) -> float | None:
        """Convert a 10.0 GPA to French scale.

        Args:
            value: GPA value (0-10.0)
            country_code: Optional country code for country-specific conversion

        Returns:
            French scale equivalent or None if conversion not possible
        """
        # Try country-specific conversion first
        if country_code:
            country_system = self.get_country_system(country_code)
            if country_system and country_system.system_type == "gpa_10":
                result = country_system.convert_numeric(value)
                if result is not None:
                    return result

        # Fall back to default ranges
        for grade_range in self.default_gpa_10_ranges:
            if grade_range.contains(value):
                return grade_range.convert(value)

        return None

    def convert_letter(self, letter: str, country_code: str | None = None) -> float | None:
        """Convert a letter grade to French scale.

        Args:
            letter: Letter grade
            country_code: Optional country code for country-specific conversion

        Returns:
            French scale equivalent or None if conversion not possible
        """
        if country_code:
            country_system = self.get_country_system(country_code)
            if country_system:
                result = country_system.convert_letter(letter)
                if result is not None:
                    return result

        return None
