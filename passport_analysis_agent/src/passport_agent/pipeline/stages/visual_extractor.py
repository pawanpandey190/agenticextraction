"""Visual extractor pipeline stage."""

from datetime import date, datetime

from ...models.passport_data import VisualExtractionResponse, VisualPassportData
from ...prompts.extraction import get_visual_extraction_prompt
from ...prompts.system import VISUAL_EXTRACTION_SYSTEM_PROMPT
from ...services.llm_service import LLMService
from ...utils.exceptions import ExtractionError
from ..base import PipelineContext, PipelineStage


class VisualExtractorStage(PipelineStage):
    """Stage 3: Extract visual zone data using Claude Vision."""

    def __init__(self, settings, llm_service: LLMService | None = None) -> None:
        """Initialize the visual extractor stage.

        Args:
            settings: Application settings
            llm_service: Optional LLM service instance
        """
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)

    @property
    def name(self) -> str:
        return "VisualExtractor"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Extract passport data from visual inspection zone.

        Uses Claude Vision to extract text from the passport image.

        Args:
            context: Pipeline context

        Returns:
            Updated context with visual data

        Raises:
            ExtractionError: If extraction fails
        """
        if not context.preprocessed_images:
            raise ExtractionError("No preprocessed images available")

        # Use the first image (passport data page)
        image_base64, mime_type = context.preprocessed_images[0]

        try:
            # Extract structured data
            response = self.llm_service.extract_with_structured_output(
                image_base64=image_base64,
                mime_type=mime_type,
                system_prompt=VISUAL_EXTRACTION_SYSTEM_PROMPT,
                response_model=VisualExtractionResponse,
            )

            # Convert to VisualPassportData
            visual_data = self._convert_response(response)
            context.visual_data = visual_data

            context.set_stage_result(
                self.name,
                {
                    "confidence": visual_data.ocr_confidence,
                    "fields_extracted": sum(
                        1
                        for v in [
                            visual_data.first_name,
                            visual_data.last_name,
                            visual_data.date_of_birth,
                            visual_data.passport_number,
                            visual_data.issuing_country,
                            visual_data.passport_expiry_date,
                            visual_data.sex,
                        ]
                        if v is not None
                    ),
                },
            )

            self.logger.info(
                "Visual data extracted",
                first_name=visual_data.first_name,
                last_name=visual_data.last_name,
                passport_number=visual_data.passport_number,
                confidence=visual_data.ocr_confidence,
            )

            return context

        except Exception as e:
            self.logger.error("Visual extraction failed", error=str(e))
            raise ExtractionError(f"Failed to extract visual data: {e}") from e

    def _convert_response(self, response: VisualExtractionResponse) -> VisualPassportData:
        """Convert extraction response to VisualPassportData.

        Args:
            response: Raw extraction response

        Returns:
            Validated VisualPassportData
        """
        # Parse dates
        date_of_birth = self._parse_date(response.date_of_birth)
        issue_date = self._parse_date(response.passport_issue_date)
        expiry_date = self._parse_date(response.passport_expiry_date)

        return VisualPassportData(
            first_name=response.first_name,
            last_name=response.last_name,
            date_of_birth=date_of_birth,
            passport_number=response.passport_number,
            issuing_country=response.issuing_country,
            nationality=response.nationality,
            passport_issue_date=issue_date,
            passport_expiry_date=expiry_date,
            sex=self._normalize_sex(response.sex),
            place_of_birth=response.place_of_birth,
            ocr_confidence=response.confidence,
        )

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string to date object.

        Supports multiple formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, etc.

        Args:
            date_str: Date string to parse

        Returns:
            Parsed date or None
        """
        if not date_str:
            return None

        # Try common formats
        formats = [
            "%Y-%m-%d",  # ISO format
            "%d/%m/%Y",  # European format
            "%m/%d/%Y",  # US format
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%Y/%m/%d",
            "%d %b %Y",  # 01 Jan 2024
            "%d %B %Y",  # 01 January 2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        self.logger.warning("Could not parse date", date_str=date_str)
        return None

    def _normalize_sex(self, sex: str | None) -> str | None:
        """Normalize sex field.

        Args:
            sex: Raw sex value

        Returns:
            Normalized sex (M, F, X) or None
        """
        if not sex:
            return None

        sex = sex.upper().strip()
        if sex in ("M", "MALE"):
            return "M"
        if sex in ("F", "FEMALE"):
            return "F"
        return "X"
