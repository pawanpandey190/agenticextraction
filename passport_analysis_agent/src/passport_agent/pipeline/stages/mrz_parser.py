"""MRZ parser pipeline stage."""

from ...services.mrz_service import MRZService
from ...utils.exceptions import MRZParseError
from ...utils.mrz_utils import format_date_to_mrz, calculate_check_digit
from ..base import PipelineContext, PipelineStage


class MRZParserStage(PipelineStage):
    """Stage 5: Parse MRZ text and validate checksums."""

    def __init__(self, settings, mrz_service: MRZService | None = None) -> None:
        """Initialize the MRZ parser stage.

        Args:
            settings: Application settings
            mrz_service: Optional MRZ service instance
        """
        super().__init__(settings)
        self.mrz_service = mrz_service or MRZService()

    @property
    def name(self) -> str:
        return "MRZParser"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Parse MRZ text into structured data.

        Validates TD3 format and all checksums.

        Args:
            context: Pipeline context

        Returns:
            Updated context with parsed MRZ data
        """
        if not context.mrz_raw_text:
            context.add_warning("STRICT VALIDATION: No MRZ text detected. Document is likely NOT a passport.")
            context.is_passport = False
            context.set_stage_result(self.name, {"parsed": False, "reason": "no_text", "is_passport": False})
            return context

        try:
            # Try to extract the two MRZ lines
            lines = self.mrz_service.extract_mrz_lines(context.mrz_raw_text)

            if lines is None:
                # Fallback: Try to reconstruct MRZ using Visual Data if available
                if context.visual_data:
                    self.logger.info("MRZ lines missing, attempting reconstruction from Visual Data")
                    lines = self._reconstruct_from_visual(context)
                
                if lines is None:
                    context.add_warning("STRICT VALIDATION: No 2-line MRZ detected. Re-classifying document as NON-PASSPORT.")
                    context.is_passport = False
                    context.set_stage_result(
                        self.name, {"parsed": False, "reason": "non_passport", "is_passport": False}
                    )
                    return context

            # Parse detected MRZ lines with VIZ witness support
            viz_witness = context.visual_data.passport_number if context.visual_data else None
            mrz_data = self.mrz_service.parse(lines, viz_witness=viz_witness)
            context.mrz_data = mrz_data

            # Log checksum results
            checksums = mrz_data.checksum_results
            self.logger.info(
                "MRZ parsed successfully",
                passport_number=mrz_data.passport_number,
                name=mrz_data.full_name,
                all_checksums_valid=checksums.all_valid,
                valid_checksums=checksums.valid_count,
            )

            context.set_stage_result(
                self.name,
                {
                    "parsed": True,
                    "checksums_valid": checksums.all_valid,
                    "valid_count": checksums.valid_count,
                },
            )

            return context

        except MRZParseError as e:
            self.logger.warning("MRZ parsing failed", error=str(e))
            context.add_warning(f"MRZ parsing failed: {e}")
            context.set_stage_result(
                self.name, {"parsed": False, "reason": "parse_error", "error": str(e)}
            )
            return context
        except Exception as e:
            self.logger.error("Unexpected error parsing MRZ", error=str(e))
            context.add_warning(f"MRZ parsing error: {e}")
            context.set_stage_result(
                self.name, {"parsed": False, "reason": "error", "error": str(e)}
            )
            return context

    def _normalize_line(self, line: str) -> str:
        """Normalize MRZ line to exactly 44 characters.

        Args:
            line: MRZ line

        Returns:
            Normalized line
        """
        # Remove any whitespace
        line = "".join(line.split()).upper()

        # Pad or truncate to 44 characters
        if len(line) < 44:
            line = line + "<" * (44 - len(line))
        elif len(line) > 44:
            line = line[:44]

        return line

    def _reconstruct_from_visual(self, context: PipelineContext) -> list[str] | None:
        """Attempt to reconstruct MRZ lines using Visual Inspection Zone (VIZ) data.
        
        Args:
            context: Pipeline context
            
        Returns:
            List of [line1, line2] if reconstruction succeeds, None otherwise
        """
        visual = context.visual_data
        if not visual:
            return None
            
        try:
            # Reconstruct Line 1: P<COUNTRY SURNAME<<GIVEN NAMES
            country = (visual.issuing_country or "UTO").upper()[:3]
            last = (visual.last_name or "").upper().replace(" ", "<")
            first = (visual.first_name or "").upper().replace(" ", "<")
            
            line1 = f"P<{country}{last}<<{first}"
            line1 = self._normalize_line(line1)
            
            # Reconstruct Line 2: 
            # 0-8: Passport Number + 9: Check
            pass_num = (visual.passport_number or "XXXXXXXXX").upper().replace(" ", "")
            pass_num = pass_num.ljust(9, "<")[:9]
            pass_check = calculate_check_digit(pass_num)
            
            # 10-12: Nationality
            nationality = (visual.nationality or country).upper()[:3]
            
            # 13-18: DOB + 19: Check
            dob = format_date_to_mrz(visual.date_of_birth) if visual.date_of_birth else "000101"
            dob_check = calculate_check_digit(dob)
            
            # 20: Sex
            sex = (visual.sex or "<").upper()[:1]
            
            # 21-26: Expiry + 27: Check
            expiry = format_date_to_mrz(visual.passport_expiry_date) if visual.passport_expiry_date else "991231"
            expiry_check = calculate_check_digit(expiry)
            
            # 28-42: Optional (Personal Number) + 43: Composite Check
            personal = "<" * 15
            
            line2_pre_composite = f"{pass_num}{pass_check}{nationality}{dob}{dob_check}{sex}{expiry}{expiry_check}{personal}"
            
            # Composite check includes: pass_num+check, dob+check, expiry+check+personal+check (if exists)
            composite_data = (
                f"{pass_num}{pass_check}"
                + f"{dob}{dob_check}"
                + f"{expiry}{expiry_check}{personal}" # Note: last char of personal is usually check for personal, here we use <
            )
            composite_check = calculate_check_digit(composite_data)
            
            line2 = f"{line2_pre_composite}{composite_check}"
            line2 = self._normalize_line(line2)
            
            return [line1, line2]
            
        except Exception as e:
            self.logger.warning("MRZ reconstruction failed", error=str(e))
            return None
