"""MRZ parsing service."""

from datetime import date

import structlog

from ..config.constants import (
    TD1_LINE_LENGTH,
    TD1_LINES,
    TD1_LINE1_DOCUMENT_NUMBER_START,
    TD1_LINE1_DOCUMENT_NUMBER_END,
    TD1_LINE1_DOCUMENT_NUMBER_CHECK,
    TD1_LINE2_DOB_START,
    TD1_LINE2_DOB_END,
    TD1_LINE2_DOB_CHECK,
    TD1_LINE2_SEX,
    TD1_LINE2_EXPIRY_START,
    TD1_LINE2_EXPIRY_END,
    TD1_LINE2_EXPIRY_CHECK,
    TD1_LINE2_NATIONALITY_START,
    TD1_LINE2_NATIONALITY_END,
    TD1_LINE2_COMPOSITE_CHECK,
    TD2_LINE_LENGTH,
    TD2_LINES,
    TD2_LINE2_DOCUMENT_NUMBER_START,
    TD2_LINE2_DOCUMENT_NUMBER_END,
    TD2_LINE2_DOCUMENT_NUMBER_CHECK,
    TD2_LINE2_NATIONALITY_START,
    TD2_LINE2_NATIONALITY_END,
    TD2_LINE2_DOB_START,
    TD2_LINE2_DOB_END,
    TD2_LINE2_DOB_CHECK,
    TD2_LINE2_SEX,
    TD2_LINE2_EXPIRY_START,
    TD2_LINE2_EXPIRY_END,
    TD2_LINE2_EXPIRY_CHECK,
    TD2_LINE2_COMPOSITE_CHECK,
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

    def parse(self, lines: list[str]) -> MRZData:
        """Parse MRZ lines automatically detecting format TD1, TD2, or TD3.
        
        Args:
            lines: List of MRZ lines (either 2 or 3 lines)
            
        Returns:
            Parsed MRZ data
            
        Raises:
            MRZParseError: If format is unknown or lines are invalid
        """
        # Normalize line lengths before format detection
        normalized_lines = []
        if len(lines) == 3:
            normalized_lines = [l.ljust(TD1_LINE_LENGTH, "<")[:TD1_LINE_LENGTH] for l in lines]
        elif len(lines) == 2:
            # Try TD3 (44) first, then TD2 (36)
            if any(len(l) >= 40 for l in lines):
                normalized_lines = [l.ljust(TD3_LINE_LENGTH, "<")[:TD3_LINE_LENGTH] for l in lines]
            else:
                normalized_lines = [l.ljust(TD2_LINE_LENGTH, "<")[:TD2_LINE_LENGTH] for l in lines]
        
        if len(normalized_lines) == 3:
            return self.parse_td1(normalized_lines[0], normalized_lines[1], normalized_lines[2])
        elif len(normalized_lines) == 2:
            if len(normalized_lines[0]) == TD3_LINE_LENGTH:
                return self.parse_td3(normalized_lines[0], normalized_lines[1])
            else:
                return self.parse_td2(normalized_lines[0], normalized_lines[1])
                
        raise MRZParseError(f"Unsupported MRZ format: {len(lines)} lines of lengths {[len(l) for l in lines]}")

    def parse_td1(self, line1: str, line2: str, line3: str) -> MRZData:
        """Parse TD1 format MRZ (Identity Card, 3 lines of 30 characters)."""
        line1, line2, line3 = line1.upper(), line2.upper(), line3.upper()
        
        # Line 1 extraction
        doc_type = line1[0:2].replace("<", "")
        issuing_country = line1[2:5]
        doc_number = line1[TD1_LINE1_DOCUMENT_NUMBER_START:TD1_LINE1_DOCUMENT_NUMBER_END]
        doc_check = line1[TD1_LINE1_DOCUMENT_NUMBER_CHECK]
        
        # Line 2 extraction
        dob_str = line2[TD1_LINE2_DOB_START:TD1_LINE2_DOB_END]
        dob_check = line2[TD1_LINE2_DOB_CHECK]
        sex = line2[TD1_LINE2_SEX]
        expiry_str = line2[TD1_LINE2_EXPIRY_START:TD1_LINE2_EXPIRY_END]
        expiry_check = line2[TD1_LINE2_EXPIRY_CHECK]
        nationality = line2[TD1_LINE2_NATIONALITY_START:TD1_LINE2_NATIONALITY_END]
        composite_check = line2[TD1_LINE2_COMPOSITE_CHECK]
        
        # Line 3 extraction (Name)
        last_name, first_name = parse_name_field(line3)
        
        # Checksums
        passport_valid = validate_check_digit(doc_number, doc_check)
        dob_valid = validate_check_digit(dob_str, dob_check)
        expiry_valid = validate_check_digit(expiry_str, expiry_check)
        
        # Composite checksum for TD1
        # ICAO 9303 Part 5: Line 1(6-14+15) + Line 2(1-7) + Line 2(9-15) + Line 2(19-29)
        composite_data = (
            line1[5:15] # Document number + check
            + line1[15:30] # Optional data 1
            + line2[0:7] # DOB + check
            + line2[8:15] # Expiry + check
            + line2[18:29] # Optional data 2
        )
        composite_valid = validate_check_digit(composite_data, composite_check)
        
        return MRZData(
            document_type=doc_type,
            issuing_country=issuing_country,
            last_name=last_name,
            first_name=first_name,
            passport_number=doc_number,
            nationality=nationality,
            date_of_birth=parse_mrz_date(dob_str, is_expiry=False),
            sex=sex_from_mrz(sex),
            expiry_date=parse_mrz_date(expiry_str, is_expiry=True),
            raw_line1=line1,
            raw_line2=line2,
            raw_line3=line3,
            checksum_results=MRZChecksumResult(
                passport_number=passport_valid,
                date_of_birth=dob_valid,
                expiry_date=expiry_valid,
                composite=composite_valid
            )
        )

    def parse_td2(self, line1: str, line2: str) -> MRZData:
        """Parse TD2 format MRZ (Identity Card / Visa, 2 lines of 36 characters)."""
        line1, line2 = line1.upper(), line2.upper()
        
        # Line 1
        doc_type = line1[0:2].replace("<", "")
        issuing_country = line1[2:5]
        name_field = line1[5:36]
        last_name, first_name = parse_name_field(name_field)
        
        # Line 2
        doc_number = line2[TD2_LINE2_DOCUMENT_NUMBER_START:TD2_LINE2_DOCUMENT_NUMBER_END]
        doc_check = line2[TD2_LINE2_DOCUMENT_NUMBER_CHECK]
        nationality = line2[TD2_LINE2_NATIONALITY_START:TD2_LINE2_NATIONALITY_END]
        dob_str = line2[TD2_LINE2_DOB_START:TD2_LINE2_DOB_END]
        dob_check = line2[TD2_LINE2_DOB_CHECK]
        sex = line2[TD2_LINE2_SEX]
        expiry_str = line2[TD2_LINE2_EXPIRY_START:TD2_LINE2_EXPIRY_END]
        expiry_check = line2[TD2_LINE2_EXPIRY_CHECK]
        composite_check = line2[TD2_LINE2_COMPOSITE_CHECK]
        
        # Checksums
        passport_valid = validate_check_digit(doc_number, doc_check)
        dob_valid = validate_check_digit(dob_str, dob_check)
        expiry_valid = validate_check_digit(expiry_str, expiry_check)
        
        composite_data = (
            line2[0:10] # Doc number + check
            + line2[13:20] # DOB + check
            + line2[21:35] # Expiry + check + optional
        )
        composite_valid = validate_check_digit(composite_data, composite_check)

        return MRZData(
            document_type=doc_type,
            issuing_country=issuing_country,
            last_name=last_name,
            first_name=first_name,
            passport_number=doc_number,
            nationality=nationality,
            date_of_birth=parse_mrz_date(dob_str, is_expiry=False),
            sex=sex_from_mrz(sex),
            expiry_date=parse_mrz_date(expiry_str, is_expiry=True),
            raw_line1=line1,
            raw_line2=line2,
            checksum_results=MRZChecksumResult(
                passport_number=passport_valid,
                date_of_birth=dob_valid,
                expiry_date=expiry_valid,
                composite=composite_valid
            )
        )

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

        # Baseline checksum validation
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

        # Try to parse Line 2 with repair if initial checksum fails
        if not checksum_results.all_valid:
            logger.info("Checksum failed, attempting repair", results=checksum_results.to_dict())
            repaired_line2 = self._repair_line2(line2)
            if repaired_line2 != line2:
                logger.info("Line 2 repaired successfully")
                line2 = repaired_line2
                # Re-extract fields from repaired line
                passport_number = line2[TD3_LINE2_PASSPORT_NUMBER_START:TD3_LINE2_PASSPORT_NUMBER_END]
                passport_check = line2[TD3_LINE2_PASSPORT_CHECK]
                nationality = line2[TD3_LINE2_NATIONALITY_START:TD3_LINE2_NATIONALITY_END]
                dob_str = line2[TD3_LINE2_DOB_START:TD3_LINE2_DOB_END]
                dob_check = line2[TD3_LINE2_DOB_CHECK]
                sex = line2[TD3_LINE2_SEX]
                expiry_str = line2[TD3_LINE2_EXPIRY_START:TD3_LINE2_EXPIRY_END]
                expiry_check = line2[TD3_LINE2_EXPIRY_CHECK]
                personal_number = line2[TD3_LINE2_PERSONAL_NUMBER_START:TD3_LINE2_PERSONAL_NUMBER_END]
                personal_check = line2[TD3_LINE2_PERSONAL_CHECK]
                composite_check = line2[TD3_LINE2_COMPOSITE_CHECK]
                
                # Re-calculate checksums for the repaired record
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

        # Parse dates again with potentially repaired strings
        try:
            date_of_birth = parse_mrz_date(dob_str, is_expiry=False)
        except MRZParseError:
            date_of_birth = date(1900, 1, 1)

        try:
            expiry_date = parse_mrz_date(expiry_str, is_expiry=True)
        except MRZParseError:
            expiry_date = date(2099, 12, 31)

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

    def extract_mrz_lines(self, text: str) -> list[str] | None:
        """Extract MRZ lines from OCR text.
        
        Detects TD1 (3x30), TD2 (2x36), or TD3 (2x44) formats.
        """
        final_lines = []
        for l in [l.strip().upper().replace(" ", "") for l in text.strip().split("\n") if l.strip()]:
            # If a line is very long (e.g. 88 or 60), it might be 2 or 3 lines joined
            if len(l) >= 60 and "P<" in l: # Likely 2x44 joined
                mid = len(l) // 2
                final_lines.append(l[:mid])
                final_lines.append(l[mid:])
            elif len(l) >= 80: # Likely 2x44 joined
                final_lines.append(l[:44])
                final_lines.append(l[44:88])
            else:
                final_lines.append(l)
        
        lines = final_lines
        
        # Look for consecutive lines with specific lengths
        # 1. Check for TD1 (3x30)
        for i in range(len(lines) - 2):
            counts = [len(lines[i+j]) for j in range(3)]
            if all(c >= 25 and c <= 35 for c in counts):
                return [lines[i+j].ljust(30, "<")[:30] for j in range(3)]
                
        # 2. Check for TD3 (2x44)
        for i in range(len(lines) - 1):
            line1 = lines[i]
            line2 = lines[i+1]
            
            # Special case: Hallucinated "P<" at start of line 2 (common OCR error)
            # If line1 starts with P< and line2 ALSO starts with P< BUT line2 contains digits
            if line1.startswith("P<") and line2.startswith("P<") and any(c.isdigit() for c in line2):
                # Check if stripping P< from line2 makes it look more like a valid Line 2
                stripped_l2 = line2[2:]
                if len(stripped_l2) >= 38: # Still long enough to potentially be a line
                    logger.info("detected_hallucinated_prefix_on_mrz_line2_stripping", 
                                line1=line1, line2=line2)
                    line2 = stripped_l2
            
            counts = [len(line1), len(line2)]
            if all(c >= 38 and c <= 50 for c in counts):
                return [line1.ljust(44, "<")[:44], line2.ljust(44, "<")[:44]]
                    
        # 3. Check for TD2 (2x36)
        for i in range(len(lines) - 1):
            counts = [len(lines[i+j]) for j in range(2)]
            if all(c >= 32 and c <= 40 for c in counts):
                 return [lines[i+j].ljust(36, "<")[:36] for j in range(2)]
                 
        return None

    def _repair_line2(self, line: str) -> str:
        """Repair common OCR errors in MRZ Line 2 using checksums.
        
        Targeted swaps: O->0, 0->O, I->1, 1->I, S->5, 5->S, B->8, 8->B.
        
        Args:
            line: 44-character Line 2 of MRZ
            
        Returns:
            Repaired line if valid checksum found, otherwise original line
        """
        repaired = list(line)
        
        # Define fields and their check digit positions in TD3 Line 2
        fields = [
            (TD3_LINE2_PASSPORT_NUMBER_START, TD3_LINE2_PASSPORT_NUMBER_END, TD3_LINE2_PASSPORT_CHECK),
            (TD3_LINE2_DOB_START, TD3_LINE2_DOB_END, TD3_LINE2_DOB_CHECK),
            (TD3_LINE2_EXPIRY_START, TD3_LINE2_EXPIRY_END, TD3_LINE2_EXPIRY_CHECK),
            (TD3_LINE2_PERSONAL_NUMBER_START, TD3_LINE2_PERSONAL_NUMBER_END, TD3_LINE2_PERSONAL_CHECK),
        ]
        
        swaps = {
            'O': '0', '0': 'O',
            'I': '1', '1': 'I',
            'S': '5', '5': 'S',
            'B': '8', '8': 'B',
            'Z': '2', '2': 'Z'
        }
        
        modified = False
        for start, end, check_idx in fields:
            field_data = "".join(repaired[start:end])
            check_digit = repaired[check_idx]
            
            # If check digit is invalid, try swapping common errors in data OR check digit
            if not validate_check_digit(field_data, check_digit):
                # 1. Try swapping characters in the data field
                field_list = list(field_data)
                found_fix = False
                for i in range(len(field_list)):
                    orig_char = field_list[i]
                    if orig_char in swaps:
                        field_list[i] = swaps[orig_char]
                        if validate_check_digit("".join(field_list), check_digit):
                            repaired[start:end] = field_list
                            modified = True
                            found_fix = True
                            break
                        field_list[i] = orig_char # Backtrack
                
                # 2. If still invalid, try swapping the check digit itself
                if not found_fix and check_digit in swaps:
                    new_check = swaps[check_digit]
                    if validate_check_digit(field_data, new_check):
                        repaired[check_idx] = new_check
                        modified = True
        
        # Finally, try repairing the composite check digit (pos 43)
        composite_data = (
            "".join(repaired[0:10])
            + "".join(repaired[13:20])
            + "".join(repaired[21:43])
        )
        composite_check = repaired[43]
        if not validate_check_digit(composite_data, composite_check):
            if composite_check in swaps:
                new_composite_check = swaps[composite_check]
                if validate_check_digit(composite_data, new_composite_check):
                    repaired[43] = new_composite_check
                    modified = True

        return "".join(repaired) if modified else line
