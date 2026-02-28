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

    def parse(self, lines: list[str], viz_witness: str | None = None) -> MRZData:
        """Parse MRZ lines automatically detecting format TD1, TD2, or TD3.
        
        Args:
            lines: List of MRZ lines (either 2 or 3 lines)
            viz_witness: Optional passport number from VIZ to use as witness
            
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
                return self.parse_td3(normalized_lines[0], normalized_lines[1], viz_witness=viz_witness)
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

    def parse_td3(self, line1: str, line2: str, viz_witness: str | None = None) -> MRZData:
        """Parse TD3 format MRZ (passport, 2 lines of 44 characters).

        Args:
            line1: First MRZ line (44 characters)
            line2: Second MRZ line (44 characters)
            viz_witness: Optional passport number from VIZ to use as witness

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
        # OR if we have a VIZ witness that disagrees (even if checksum is "valid" due to collision)
        should_repair = not checksum_results.all_valid
        if not should_repair and viz_witness:
            # Check for collision: MRZ valid but different from VIZ
            clean_pass = passport_number.replace("<", "").strip()
            clean_viz = viz_witness.replace("<", "").strip()
            if clean_pass != clean_viz:
                logger.info("Checksum valid but MRZ disagrees with VIZ witness, attempting collision-aware repair", 
                           mrz=clean_pass, viz=clean_viz)
                should_repair = True

        if should_repair:
            logger.info("Attempting line repair", checksum_valid=checksum_results.all_valid, has_viz=viz_witness is not None)
            repaired_line2 = self._repair_line2(line2, viz_witness=viz_witness)
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

    def _repair_line2(self, line: str, viz_witness: str | None = None) -> str:
        """Repair common OCR errors in MRZ Line 2 using checksums and optional VIZ witness.
        
        Handles multiple character swaps using a depth-limited search for fields where 
        checksums fail or disagree with VIZ.
        
        Targeted swaps: O<->0, I<->1, S<->5, B<->8, Z<->2.
        
        Args:
            line: 44-character Line 2 of MRZ
            viz_witness: Optional passport number from VIZ to use as witness
            
        Returns:
            Repaired line if valid checksum found, otherwise original line
        """
        repaired = list(line)
        modified = False
        
        # Define fields and their check digit positions in TD3 Line 2
        # (start, end, check_idx, is_numeric_only)
        fields = [
            (TD3_LINE2_PASSPORT_NUMBER_START, TD3_LINE2_PASSPORT_NUMBER_END, TD3_LINE2_PASSPORT_CHECK, False),
            (TD3_LINE2_DOB_START, TD3_LINE2_DOB_END, TD3_LINE2_DOB_CHECK, True),
            (TD3_LINE2_EXPIRY_START, TD3_LINE2_EXPIRY_END, TD3_LINE2_EXPIRY_CHECK, True),
            (TD3_LINE2_PERSONAL_NUMBER_START, TD3_LINE2_PERSONAL_NUMBER_END, TD3_LINE2_PERSONAL_CHECK, False),
        ]
        
        swaps = {
            'O': '0', '0': 'O',
            'I': '1', '1': 'I',
            'S': '5', '5': 'S',
            'B': '8', '8': 'B',
            'Z': '2', '2': 'Z'
        }
        
        for start, end, check_idx, numeric_only in fields:
            field_data = "".join(repaired[start:end])
            check_digit = repaired[check_idx]
            
            is_passport_field = (start == TD3_LINE2_PASSPORT_NUMBER_START)
            witness = viz_witness if is_passport_field else None
            
            # Check if current field is valid and matches witness
            is_valid = validate_check_digit(field_data, check_digit)
            matches_witness = True
            if witness:
                matches_witness = (field_data.replace("<", "").strip() == witness.replace("<", "").strip())
            
            if not is_valid or not matches_witness:
                # Attempt to find a combination that satisfies the checksum
                # and matches witness if available.
                best_fix = self._find_best_field_fix(
                    field_data, 
                    check_digit, 
                    swaps, 
                    numeric_only=numeric_only,
                    witness=witness
                )
                
                if best_fix:
                    new_field, new_check = best_fix
                    if new_field != field_data or new_check != check_digit:
                        repaired[start:end] = list(new_field)
                        repaired[check_idx] = new_check
                        modified = True
                        logger.info("Field repaired", field=new_field, check=new_check, original=field_data)
        
        # Finally, try repairing the composite check digit (pos 43)
        composite_data = (
            "".join(repaired[0:10])
            + "".join(repaired[13:20])
            + "".join(repaired[21:43])
        )
        composite_check = repaired[43]
        if not validate_check_digit(composite_data, composite_check):
            # Try swapping in composite data or check digit
            # For simplicity, we just try swapping the composite check digit itself for now
            if composite_check in swaps:
                new_composite_check = swaps[composite_check]
                if validate_check_digit(composite_data, new_composite_check):
                    repaired[43] = new_composite_check
                    modified = True

        return "".join(repaired) if modified else line

    def _find_best_field_fix(
        self, 
        field_data: str, 
        check_digit: str, 
        swaps_map: dict[str, str], 
        numeric_only: bool = False,
        witness: str | None = None
    ) -> tuple[str, str] | None:
        """Find the best combination of character swaps to satisfy checksum and witness."""
        
        # If witness is provided, prioritize it
        if witness:
            # Normalize witness to 9 chars with < padding
            norm_witness = witness.replace("<", "").strip().upper().ljust(9, "<")[:9]
            witness_check = calculate_check_digit(norm_witness)
            
            # Check if witness itself (as digits) satisfies the current checksum (if it were allowed)
            # This handles the case where OCR read 'B' (letter) but witness is '8' (digit)
            if validate_check_digit(norm_witness, str(witness_check)):
                # If the witness is valid and we can reach it via swaps, take it!
                can_reach = True
                for i in range(len(field_data)):
                    if field_data[i] != norm_witness[i]:
                        if field_data[i] not in swaps_map or swaps_map[field_data[i]] != norm_witness[i]:
                            can_reach = False
                            break
                
                if can_reach:
                    return norm_witness, str(witness_check)

        # General search for checksum matches
        # Generate possible swap indices
        swap_indices = [i for i, char in enumerate(field_data) if char in swaps_map]
        check_can_swap = check_digit in swaps_map
        
        # Use a simple recursion to try combinations (max 2^swap_indices)
        # We limit depth to avoid explosion, though fields are small (9)
        results = []
        
        def explore(idx_ptr, current_field, current_check):
            if validate_check_digit(current_field, current_check):
                # Count swaps from original
                swap_count = 0
                for i in range(len(current_field)):
                    if current_field[i] != field_data[i]: swap_count += 1
                if current_check != check_digit: swap_count += 1
                
                results.append((swap_count, current_field, current_check))
                return

            if idx_ptr >= len(swap_indices):
                # Try swapping check digit if we haven't already
                if check_can_swap and current_check == check_digit:
                    explore(idx_ptr, current_field, swaps_map[check_digit])
                return

            # Option 1: Don't swap this character
            explore(idx_ptr + 1, current_field, current_check)
            
            # Option 2: Swap this character
            idx = swap_indices[idx_ptr]
            new_field = current_field[:idx] + swaps_map[current_field[idx]] + current_field[idx+1:]
            explore(idx_ptr + 1, new_field, current_check)

        # Limit search space if too many swap candidates (unlikely for 9 chars)
        if len(swap_indices) > 5:
            swap_indices = swap_indices[:5]
            
        explore(0, field_data, check_digit)
        
        if not results:
            return None
            
        # Prioritize minimum swaps
        results.sort(key=lambda x: x[0])
        return results[0][1], results[0][2]
