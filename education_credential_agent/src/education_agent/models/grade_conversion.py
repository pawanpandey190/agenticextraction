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
    foundation_minimum_pct: float | None = Field(
        default=None,
        description="Foundation minimum threshold expressed as a quality percentage (0-100). Student's normalized score must be >= this to qualify (≥ 8/20 French equivalent).",
    )
    foundation_minimum_letter: str | None = Field(
        default=None,
        description="Foundation minimum as a letter grade (for letter-grade systems). Student must have this grade or better.",
    )
    foundation_minimum_gpa4: float | None = Field(
        default=None,
        description="Foundation minimum as a GPA (0-4.0).",
    )
    foundation_minimum_gpa10: float | None = Field(
        default=None,
        description="Foundation minimum as a GPA/CGPA (0-10.0).",
    )

    def convert_numeric(self, value: float) -> float | None:
        """Convert a numeric grade to French scale.

        Args:
            value: The numeric grade value

        Returns:
            French scale equivalent or None if no matching range
        """
        # German specific formula: French = ((5 - German) / 4) * 20
        if self.system_type == "german_5":
            # German grades are 1.0 (best) to 5.0 (fail)
            # Clip between 1.0 and 5.0
            val = max(1.0, min(5.0, value))
            return round(((5.0 - val) / 4.0) * 20.0, 2)

        if not self.numeric_ranges:
            return None

        # Sort ranges by min_value to ensure consistent overlap handling if any
        # though ideally they should be continuous.
        for grade_range in self.numeric_ranges:
            if grade_range.contains(value):
                return grade_range.convert(value)

        return None

    def _find_letter_mapping(self, letter: str) -> tuple[int, LetterGradeMapping] | tuple[None, None]:
        """Find the mapping for a letter grade using exact, partial, or description match.
        
        Args:
            letter: The letter grade string to match
            
        Returns:
            Tuple of (index, mapping) or (None, None) if not found
        """
        if not self.letter_mappings:
            return None, None
            
        letter_upper = (letter or "").upper().strip()
        if not letter_upper:
            return None, None
        
        # 1. Try exact match on letter
        for i, mapping in enumerate(self.letter_mappings):
            if mapping.letter.upper() == letter_upper:
                return i, mapping
                
        # 2. Try exact match on description
        for i, mapping in enumerate(self.letter_mappings):
            if mapping.description and mapping.description.upper() == letter_upper:
                return i, mapping
                
        # 3. Try partial match on letter (e.g., "D+ (PLUS)" matches "D+")
        # Match most specific (longest) prefix first
        sorted_mappings = sorted(
            enumerate(self.letter_mappings), 
            key=lambda x: len(x[1].letter), 
            reverse=True
        )
        for i, mapping in sorted_mappings:
            m_letter = mapping.letter.upper()
            if letter_upper.startswith(m_letter):
                remaining = letter_upper[len(m_letter):].strip()
                if not remaining or not remaining[0].isalnum():
                    return i, mapping
                    
        # 4. Try partial match on description
        for i, mapping in enumerate(self.letter_mappings):
            if mapping.description:
                desc_upper = mapping.description.upper()
                if letter_upper.startswith(desc_upper):
                    remaining = letter_upper[len(desc_upper):].strip()
                    if not remaining or not remaining[0].isalnum():
                        return i, mapping
        
        return None, None

    def convert_letter(self, letter: str) -> float | None:
        """Convert a letter grade to French scale.

        Args:
            letter: The letter grade

        Returns:
            French scale equivalent or None if not found
        """
        _, mapping = self._find_letter_mapping(letter)
        return mapping.get_french_equivalent() if mapping else None

    def get_letter_rank(self, letter: str) -> int | None:
        """Return the rank (index) of a letter in the letter_mappings list.
        Lower index = better grade (mappings are ordered best-first).
        """
        index, _ = self._find_letter_mapping(letter)
        return index

    def check_threshold(
        self,
        numeric_value: float | None,
        grading_system: str,
        max_possible: float | None,
        original_value: str | None,
    ) -> tuple[bool, str]:
        """Check if the student score meets the country foundation minimum threshold.

        Args:
            numeric_value: Numeric grade value
            grading_system: Grading system string (GradingSystem enum value)
            max_possible: Maximum possible value in the system
            original_value: Original grade string from document

        Returns:
            (meets_threshold: bool, reason: str)
        """
        country_name = self.country_name
        gs = (grading_system or "OTHER").upper()

        # ── 1. Letter grade threshold comparison ────────────────────────────────
        if self.foundation_minimum_letter and (gs in ("LETTER_GRADE", "UK_HONORS") or (original_value and not original_value.replace(".", "").isdigit())):
            threshold_letter = self.foundation_minimum_letter
            student_letter = (original_value or "").strip()

            threshold_rank = self.get_letter_rank(threshold_letter)
            student_rank = self.get_letter_rank(student_letter)

            if threshold_rank is None:
                return True, f"Threshold letter '{threshold_letter}' not found in {country_name} mapping — defaulting to PASS."
            if student_rank is None:
                return False, f"Student grade '{student_letter}' not recognized in {country_name} grade system."

            meets = student_rank <= threshold_rank  # lower index = better grade
            direction = "≥" if meets else "<"
            verdict = "meets" if meets else "does not meet"
            return meets, (
                f"Student grade '{student_letter}' {verdict} {country_name}'s "
                f"foundation minimum of '{threshold_letter}' → {direction} 8/20."
            )

        if numeric_value is None:
            return False, f"No numeric grade available to compare against {country_name} threshold."

        # ── 2. Handle scale-specific comparisons (Direct Comparison) ───────────
        
        # Marks/Total case: Always convert to percentage first
        if max_possible and max_possible > 0 and gs not in ("PERCENTAGE", "GPA_4", "GPA_10", "FRENCH_20"):
            normalized_pct = (numeric_value / max_possible) * 100.0
            threshold = self.foundation_minimum_pct or 40.0
            meets = normalized_pct >= threshold
            direction = "≥" if meets else "<"
            verdict = "passes" if meets else "does not reach"
            return meets, (
                f"{numeric_value}/{max_possible} ({normalized_pct:.1f}%) {verdict} {country_name}'s "
                f"foundation minimum of {threshold:.0f}% → {direction} 8/20."
            )

        # Direct GPA 4.0 comparison
        if gs == "GPA_4" and self.foundation_minimum_gpa4 is not None:
            threshold = self.foundation_minimum_gpa4
            meets = numeric_value >= threshold
            direction = "≥" if meets else "<"
            return meets, f"GPA {numeric_value}/4.0 {'meets' if meets else 'does not meet'} {country_name}'s minimum of {threshold}/4.0 → {direction} 8/20."

        # Direct GPA 10.0 / CGPA comparison
        if gs == "GPA_10" and self.foundation_minimum_gpa10 is not None:
            threshold = self.foundation_minimum_gpa10
            meets = numeric_value >= threshold
            direction = "≥" if meets else "<"
            return meets, f"CGPA {numeric_value}/10.0 {'meets' if meets else 'does not meet'} {country_name}'s minimum of {threshold}/10.0 → {direction} 8/20."

        # Direct Percentage comparison
        if gs == "PERCENTAGE" and self.foundation_minimum_pct is not None:
            threshold = self.foundation_minimum_pct
            meets = numeric_value >= threshold
            direction = "≥" if meets else "<"
            return meets, f"Grade {numeric_value}% {'meets' if meets else 'does not meet'} {country_name}'s minimum of {threshold:.0f}% → {direction} 8/20."

        # ── 3. Fallback: Normalization to Quality Percentage ─────────────────
        normalized = normalize_to_quality_pct(numeric_value, grading_system, max_possible)
        if normalized is None:
            return False, f"Could not evaluate grade '{original_value}' for {country_name}."

        threshold = self.foundation_minimum_pct or 40.0
        meets = normalized >= threshold

        direction = "≥" if meets else "<"
        verdict = "passes" if meets else "does not reach"
        return meets, (
            f"Normalized score {normalized:.1f}% {verdict} {country_name}'s "
            f"threshold of {threshold:.0f}% → {direction} 8/20."
        )


def normalize_to_quality_pct(
    numeric_value: float,
    grading_system: str,
    max_possible: float | None,
) -> float | None:
    """Normalize any grade to a 0-100 quality percentage for threshold comparison.

    Higher = better for all systems (inverted scales are flipped).

    Args:
        numeric_value: The numeric grade value
        grading_system: GradingSystem enum value string (e.g. 'PERCENTAGE', 'GPA_4')
        max_possible: Maximum possible grade value in the system

    Returns:
        Normalized quality percentage (0-100) or None if cannot normalize
    """
    if numeric_value is None:
        return None

    gs = (grading_system or "").upper()

    # If max_possible is explicitly given and system is not inverted — always use it
    # This handles dynamic "marks/total" cases like 450/600
    if max_possible and max_possible > 0 and gs not in ("GERMAN_5", "PHILIPPINE_5"):
        return min(100.0, (numeric_value / max_possible) * 100.0)

    if gs == "PERCENTAGE":
        return min(100.0, max(0.0, numeric_value))

    if gs == "GPA_4":
        return min(100.0, (numeric_value / 4.0) * 100.0)

    if gs == "GPA_10":
        return min(100.0, (numeric_value / 10.0) * 100.0)

    if gs == "FRENCH_20":
        return min(100.0, (numeric_value / 20.0) * 100.0)

    if gs == "GERMAN_5":
        # Inverted: 1.0=best=100%, 5.0=worst=0%
        val = max(1.0, min(5.0, numeric_value))
        return round(((5.0 - val) / 4.0) * 100.0, 2)

    # Fallback: if max_possible given use it
    if max_possible and max_possible > 0:
        return min(100.0, (numeric_value / max_possible) * 100.0)

    # Last resort: treat as percentage if in 0-100
    if 0 <= numeric_value <= 100:
        return float(numeric_value)

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
        """Convert a percentage to French scale using exact formula: (Score/100) * 20.

        Args:
            value: Percentage value (0-100)
            country_code: Optional country code (ignored as we use universal formula)

        Returns:
            French scale equivalent or None if conversion not possible
        """
        # Cap percentage at 100
        value = max(0.0, min(value, 100.0))
        
        # Universal Formula: (Score / 100) * 20
        return round((value / 100.0) * 20.0, 2)

    def convert_gpa_4(self, value: float, country_code: str | None = None) -> float | None:
        """Convert a 4.0 GPA to French scale using exact formula: (Score/4.0) * 20.

        Args:
            value: GPA value (0-4.0)
            country_code: Optional country code (ignored as we use universal formula)

        Returns:
            French scale equivalent or None if conversion not possible
        """
        # Cap GPA at 4.0
        value = max(0.0, min(value, 4.0))

        # Universal Formula: (Score / 4) * 20
        return round((value / 4.0) * 20.0, 2)

    def convert_gpa_10(self, value: float, country_code: str | None = None) -> float | None:
        """Convert a 10.0 GPA to French scale using exact formula: (Score/10.0) * 20.

        Args:
            value: GPA value (0-10.0)
            country_code: Optional country code (ignored as we use universal formula)

        Returns:
            French scale equivalent or None if conversion not possible
        """
        # Cap GPA at 10.0
        value = max(0.0, min(value, 10.0))

        # Universal Formula: (Score / 10) * 20
        return round((value / 10.0) * 20.0, 2)

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
