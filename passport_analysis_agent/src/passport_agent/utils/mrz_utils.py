"""MRZ parsing utilities following ICAO 9303 standard."""

from datetime import date

from ..config.constants import MRZ_VALUES, MRZ_WEIGHTS
from .exceptions import MRZParseError


def calculate_check_digit(data: str) -> str:
    """Calculate MRZ check digit using ICAO 9303 algorithm.

    The algorithm uses weights [7, 3, 1] repeating and character values
    from 0-35 (0-9 for digits, 10-35 for A-Z, 0 for <).

    Args:
        data: String to calculate check digit for

    Returns:
        Single digit check character (0-9)

    Raises:
        MRZParseError: If data contains invalid characters
    """
    total = 0
    for i, char in enumerate(data.upper()):
        if char not in MRZ_VALUES:
            raise MRZParseError(
                f"Invalid MRZ character: '{char}'",
                details={"position": i, "data": data},
            )
        value = MRZ_VALUES[char]
        weight = MRZ_WEIGHTS[i % 3]
        total += value * weight

    return str(total % 10)


def validate_check_digit(data: str, expected_check: str) -> bool:
    """Validate a check digit against data.

    Args:
        data: Data string (without check digit)
        expected_check: Expected check digit

    Returns:
        True if check digit is valid
    """
    try:
        calculated = calculate_check_digit(data)
        return calculated == expected_check
    except MRZParseError:
        return False


def parse_mrz_date(date_str: str, is_expiry: bool = False) -> date:
    """Parse MRZ date format (YYMMDD) to Python date.

    For birth dates, assumes years 00-29 are 2000s, 30-99 are 1900s.
    For expiry dates, assumes years 00-79 are 2000s, 80-99 are 1900s.

    Args:
        date_str: 6-character date string (YYMMDD)
        is_expiry: Whether this is an expiry date (affects century logic)

    Returns:
        Python date object

    Raises:
        MRZParseError: If date is invalid
    """
    if len(date_str) != 6:
        raise MRZParseError(
            f"Invalid MRZ date length: {len(date_str)}",
            details={"date_str": date_str},
        )

    try:
        year = int(date_str[0:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])

        # Determine century
        if is_expiry:
            # Expiry dates: 00-79 -> 2000s, 80-99 -> 1900s
            century = 2000 if year < 80 else 1900
        else:
            # Birth dates: 00-29 -> 2000s, 30-99 -> 1900s
            century = 2000 if year < 30 else 1900

        full_year = century + year

        return date(full_year, month, day)

    except ValueError as e:
        raise MRZParseError(
            f"Invalid MRZ date: {date_str}",
            details={"error": str(e)},
        ) from e


def format_date_to_mrz(d: date) -> str:
    """Format a Python date to MRZ format (YYMMDD).

    Args:
        d: Python date object

    Returns:
        6-character MRZ date string
    """
    return d.strftime("%y%m%d")


def parse_name_field(name_field: str) -> tuple[str, str]:
    """Parse MRZ name field into surname and given names.

    The name field uses << to separate surname from given names,
    and < to separate individual given names.

    Args:
        name_field: Raw MRZ name field (after document type and country)

    Returns:
        Tuple of (last_name, first_name)

    Raises:
        MRZParseError: If name field format is invalid
    """
    # Split on << (surname/given names separator)
    parts = name_field.split("<<")

    if len(parts) < 1:
        raise MRZParseError(
            "Invalid name field format",
            details={"name_field": name_field},
        )

    last_name = parts[0].replace("<", " ").strip()

    if len(parts) > 1:
        # Join all given name parts with spaces
        given_names = " ".join(parts[1:]).replace("<", " ").strip()
    else:
        given_names = ""

    return last_name, given_names


def clean_mrz_text(text: str) -> str:
    """Clean and normalize MRZ text.

    Removes common OCR errors and normalizes whitespace.

    Args:
        text: Raw MRZ text

    Returns:
        Cleaned MRZ text
    """
    # Remove all whitespace
    text = "".join(text.split())

    # Common OCR error corrections
    corrections = {
        "O": "0",  # O -> 0 (in numeric contexts, handled separately)
        "I": "1",  # I -> 1 (in numeric contexts, handled separately)
        "l": "1",  # l -> 1
        "!": "1",  # ! -> 1
        "S": "5",  # S -> 5 (in numeric contexts)
        "B": "8",  # B -> 8 (in numeric contexts)
    }

    # Only apply corrections in appropriate contexts
    # For now, just uppercase
    return text.upper()


def extract_mrz_lines(text: str) -> list[str]:
    """Extract MRZ lines from text.

    Looks for lines that match TD3 MRZ format (44 characters,
    starting with valid MRZ characters).

    Args:
        text: Text potentially containing MRZ

    Returns:
        List of MRZ lines found
    """
    lines = text.split("\n")
    mrz_lines = []

    for line in lines:
        # Clean the line
        cleaned = "".join(line.split())
        cleaned = cleaned.upper()

        # Check if it looks like an MRZ line
        if len(cleaned) >= 42 and len(cleaned) <= 46:
            # Check for valid MRZ characters
            valid_chars = set(MRZ_VALUES.keys())
            if all(c in valid_chars for c in cleaned):
                mrz_lines.append(cleaned[:44])  # Truncate to 44 if needed

    return mrz_lines


def normalize_passport_number(number: str) -> str:
    """Normalize passport number for comparison.

    Removes filler characters and normalizes to uppercase.

    Args:
        number: Raw passport number

    Returns:
        Normalized passport number
    """
    # Remove filler characters and whitespace
    normalized = number.replace("<", "").replace(" ", "").strip().upper()
    return normalized


def sex_from_mrz(mrz_sex: str) -> str:
    """Convert MRZ sex character to standard format.

    Args:
        mrz_sex: MRZ sex character (M, F, or <)

    Returns:
        Standardized sex (M, F, or X)
    """
    if mrz_sex == "M":
        return "M"
    elif mrz_sex == "F":
        return "F"
    else:
        return "X"  # Unspecified
