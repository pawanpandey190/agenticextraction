"""MRZ parser pipeline stage."""

from ...services.mrz_service import MRZService
from ...utils.exceptions import MRZParseError
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
            context.add_warning("No MRZ text to parse")
            context.set_stage_result(self.name, {"parsed": False, "reason": "no_text"})
            return context

        try:
            # Try to extract the two MRZ lines
            lines = self.mrz_service.extract_mrz_lines(context.mrz_raw_text)

            if lines is None:
                context.add_warning("Could not identify valid MRZ lines")
                context.set_stage_result(
                    self.name, {"parsed": False, "reason": "invalid_lines"}
                )
                return context

            line1, line2 = lines

            # Ensure proper length
            line1 = self._normalize_line(line1)
            line2 = self._normalize_line(line2)

            # Parse TD3 format
            mrz_data = self.mrz_service.parse_td3(line1, line2)
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
