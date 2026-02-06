"""MRZ parsing service."""

from datetime import date

import structlog

from ..config.constants import (
    TD3_LINE2_COMPOSITE_CHECK,
    TD3_LINE2_DOB_CHECK,
    TD3_LINE2_DOB_END,
    TD3_LINE2_DOB_START,
    TD3_LINE2_EXPIRY_CHECK,
    TD3_LINE2_EXPIRY_END,
    TD3_LINE2_EXPIRY_START,
    TD3_LINE2_NATIONALITY_END,
    TD3_LINE2_NATIONALITY_START,
    TD3_LINE2_PASSPORT_CHECK,
    TD3_LINE2_PASSPORT_NUMBER_END,
    TD3_LINE2_PASSPORT_NUMBER_START,
    TD3_LINE2_PERSONAL_CHECK,
    TD3_LINE2_PERSONAL_NUMBER_END,
    TD3_LINE2_PERSONAL_NUMBER_START,
    TD3_LINE2_SEX,
    TD3_LINE_LENGTH,
)
from ..models.mrz import MRZChecksumResult, MRZData
from ..utils.exceptions import MRZParseError
from ..utils.mrz_utils import (
    calculate_check_digit,
    parse_mrz_date,
    parse_name_field,
    sex_from_mrz,
    validate_check_digit,
)

logger = structlog.get_logger(__name__)


class MRZService:
    """Service for parsing and validating MRZ data."""

    def parse_td3(self, line1: str, line2: str) -> MRZData:
        """Parse TD3 format MRZ (passport, 2 lines of 44 characters).

        Args:
            line1: First MRZ line (44 characters)
            line2: Second MRZ line (44 characters)

        Returns:
            Parsed MRZ data

        Raises:
            MRZParseError: If MRZ format is invalid
        """
        # Validate line lengths
        if len(line1) != TD3_LINE_LENGTH:
            raise MRZParseError(
                f"Line 1 must be {TD3_LINE_LENGTH} characters, got {len(line1)}",
                details={"line1": line1},
            )
        if len(line2) != TD3_LINE_LENGTH:
            raise MRZParseError(
                f"Line 2 must be {TD3_LINE_LENGTH} characters, got {len(line2)}",
                details={"line2": line2},
            )

        # Uppercase and clean
        line1 = line1.upper()
        line2 = line2.upper()

        # Parse Line 1
        document_type = line1[0:2].replace("<", "").strip()
        if not document_type:
            document_type = "P"

        issuing_country = line1[2:5]
        name_field = line1[5:44]

        try:
            last_name, first_name = parse_name_field(name_field)
        except Exception as e:
            raise MRZParseError(f"Failed to parse name field: {e}") from e

        # Parse Line 2
        passport_number = line2[
            TD3_LINE2_PASSPORT_NUMBER_START:TD3_LINE2_PASSPORT_NUMBER_END
        ]
        passport_check = line2[TD3_LINE2_PASSPORT_CHECK]

        nationality = line2[TD3_LINE2_NATIONALITY_START:TD3_LINE2_NATIONALITY_END]

        dob_str = line2[TD3_LINE2_DOB_START:TD3_LINE2_DOB_END]
        dob_check = line2[TD3_LINE2_DOB_CHECK]

        sex = line2[TD3_LINE2_SEX]

        expiry_str = line2[TD3_LINE2_EXPIRY_START:TD3_LINE2_EXPIRY_END]
        expiry_check = line2[TD3_LINE2_EXPIRY_CHECK]

        personal_number = line2[
            TD3_LINE2_PERSONAL_NUMBER_START:TD3_LINE2_PERSONAL_NUMBER_END
        ]
        personal_check = line2[TD3_LINE2_PERSONAL_CHECK]
        composite_check = line2[TD3_LINE2_COMPOSITE_CHECK]

        # Parse dates
        try:
            date_of_birth = parse_mrz_date(dob_str, is_expiry=False)
        except MRZParseError:
            logger.warning("Failed to parse DOB, using placeholder", dob=dob_str)
            date_of_birth = date(1900, 1, 1)

        try:
            expiry_date = parse_mrz_date(expiry_str, is_expiry=True)
        except MRZParseError:
            logger.warning(
                "Failed to parse expiry date, using placeholder", expiry=expiry_str
            )
            expiry_date = date(2099, 12, 31)

        # Validate checksums
        checksum_results = self._validate_checksums(
            passport_number=passport_number,
            passport_check=passport_check,
            dob_str=dob_str,
            dob_check=dob_check,
            expiry_str=expiry_str,
            expiry_check=expiry_check,
            personal_number=personal_number,
            personal_check=personal_check,
            composite_check=composite_check,
            line2=line2,
        )

        # Clean personal number
        clean_personal = personal_number.replace("<", "").strip()

        return MRZData(
            document_type=document_type,
            issuing_country=issuing_country,
            last_name=last_name,
            first_name=first_name,
            passport_number=passport_number,
            nationality=nationality,
            date_of_birth=date_of_birth,
            sex=sex_from_mrz(sex),
            expiry_date=expiry_date,
            personal_number=clean_personal if clean_personal else None,
            raw_line1=line1,
            raw_line2=line2,
            checksum_results=checksum_results,
        )

    def _validate_checksums(
        self,
        passport_number: str,
        passport_check: str,
        dob_str: str,
        dob_check: str,
        expiry_str: str,
        expiry_check: str,
        personal_number: str,
        personal_check: str,
        composite_check: str,
        line2: str,
    ) -> MRZChecksumResult:
        """Validate all MRZ checksums.

        Args:
            Various MRZ fields and their check digits

        Returns:
            MRZChecksumResult with validation status
        """
        # Passport number check (positions 0-8, check at 9)
        passport_valid = validate_check_digit(passport_number, passport_check)

        # Date of birth check (positions 13-18, check at 19)
        dob_valid = validate_check_digit(dob_str, dob_check)

        # Expiry date check (positions 21-26, check at 27)
        expiry_valid = validate_check_digit(expiry_str, expiry_check)

        # Composite check
        # Includes: passport number + check (0-9), DOB + check (13-19), expiry + check + personal (21-42)
        composite_data = (
            line2[0:10]  # Passport number + check
            + line2[13:20]  # DOB + check
            + line2[21:43]  # Expiry + check + personal number + check
        )
        composite_valid = validate_check_digit(composite_data, composite_check)

        logger.debug(
            "MRZ checksum validation",
            passport_valid=passport_valid,
            dob_valid=dob_valid,
            expiry_valid=expiry_valid,
            composite_valid=composite_valid,
        )

        return MRZChecksumResult(
            passport_number=passport_valid,
            date_of_birth=dob_valid,
            expiry_date=expiry_valid,
            composite=composite_valid,
        )

    def extract_mrz_lines(self, text: str) -> tuple[str, str] | None:
        """Extract MRZ lines from OCR text.

        Looks for two consecutive lines that look like TD3 MRZ.

        Args:
            text: OCR text that may contain MRZ

        Returns:
            Tuple of (line1, line2) if found, None otherwise
        """
        lines = text.strip().split("\n")
        mrz_candidates = []

        for line in lines:
            # Clean the line
            cleaned = "".join(line.split()).upper()

            # Check if it looks like MRZ (mostly valid chars, right length)
            if len(cleaned) >= 42 and len(cleaned) <= 46:
                # Check for high proportion of valid MRZ characters
                valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")
                char_count = sum(1 for c in cleaned if c in valid_chars)
                if char_count >= len(cleaned) * 0.9:
                    mrz_candidates.append(cleaned[:44])

        # Look for consecutive TD3 lines
        for i in range(len(mrz_candidates) - 1):
            line1 = mrz_candidates[i]
            line2 = mrz_candidates[i + 1]

            # Line 1 should start with P (passport) or similar
            # Line 2 should have numbers in expected positions
            if line1[0] == "P" or line1[0:2] == "P<":
                # Additional validation: line 2 should have digits in DOB position
                if any(c.isdigit() for c in line2[13:19]):
                    return line1, line2

        # If no consecutive lines found, try to return any two lines that look valid
        if len(mrz_candidates) >= 2:
            return mrz_candidates[0], mrz_candidates[1]

        return None
