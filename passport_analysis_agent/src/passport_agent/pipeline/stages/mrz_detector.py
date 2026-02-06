"""MRZ detector pipeline stage."""

from ...prompts.extraction import get_mrz_extraction_prompt
from ...prompts.system import MRZ_EXTRACTION_SYSTEM_PROMPT
from ...services.llm_service import LLMService
from ..base import PipelineContext, PipelineStage


class MRZDetectorStage(PipelineStage):
    """Stage 4: Detect and extract raw MRZ text from image."""

    def __init__(self, settings, llm_service: LLMService | None = None) -> None:
        """Initialize the MRZ detector stage.

        Args:
            settings: Application settings
            llm_service: Optional LLM service instance
        """
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)

    @property
    def name(self) -> str:
        return "MRZDetector"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Detect and extract MRZ text from passport image.

        Uses Claude Vision to locate and read the MRZ zone.

        Args:
            context: Pipeline context

        Returns:
            Updated context with raw MRZ text

        Raises:
            ExtractionError: If MRZ detection fails
        """
        if not context.preprocessed_images:
            context.add_warning("No preprocessed images for MRZ detection")
            return context

        # Use the first image
        image_base64, mime_type = context.preprocessed_images[0]

        try:
            # Extract MRZ text using Claude Vision
            mrz_text = self.llm_service.extract_from_image(
                image_base64=image_base64,
                mime_type=mime_type,
                system_prompt=MRZ_EXTRACTION_SYSTEM_PROMPT,
                extraction_prompt=get_mrz_extraction_prompt(),
            )

            # Clean the extracted text
            mrz_text = self._clean_mrz_text(mrz_text)

            if mrz_text:
                context.mrz_raw_text = mrz_text
                context.set_stage_result(
                    self.name,
                    {
                        "mrz_found": True,
                        "text_length": len(mrz_text),
                    },
                )
                self.logger.info("MRZ text detected", length=len(mrz_text))
            else:
                context.add_warning("No MRZ text detected in image")
                context.set_stage_result(self.name, {"mrz_found": False})
                self.logger.warning("No MRZ detected")

            return context

        except Exception as e:
            self.logger.warning("MRZ detection failed", error=str(e))
            context.add_warning(f"MRZ detection failed: {e}")
            context.set_stage_result(self.name, {"mrz_found": False, "error": str(e)})
            return context

    def _clean_mrz_text(self, text: str) -> str:
        """Clean extracted MRZ text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned MRZ text
        """
        if not text:
            return ""

        lines = []
        for line in text.strip().split("\n"):
            # Remove whitespace and normalize
            cleaned = "".join(line.split()).upper()

            # Check if it looks like MRZ
            if len(cleaned) >= 30:
                # Replace common OCR errors
                cleaned = cleaned.replace("O", "0")  # Only in numeric contexts
                lines.append(cleaned)

        return "\n".join(lines)
