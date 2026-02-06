"""OCR processing stage."""

from ...config.settings import Settings
from ...services.llm_service import LLMService
from ...services.ocr_service import create_ocr_service
from ...utils.exceptions import OCRError
from ..base import PipelineContext, PipelineStage


class OCRProcessorStage(PipelineStage):
    """Stage for extracting text from document images."""

    def __init__(self, settings: Settings, llm_service: LLMService | None = None) -> None:
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)
        self.ocr_service = create_ocr_service(settings, self.llm_service)

    @property
    def name(self) -> str:
        return "ocr_processor"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Extract text from document pages.

        Args:
            context: Pipeline context

        Returns:
            Updated context with extracted text

        Raises:
            OCRError: If text extraction fails
        """
        if context.document is None:
            raise OCRError("No document loaded")

        if not context.document.pages:
            raise OCRError("Document has no pages")

        # Prepare images for OCR
        images = [
            (page.image_data, page.mime_type)
            for page in context.document.pages
        ]

        # Extract text from all pages
        extracted_text = self.ocr_service.extract_text_from_multiple(images)

        context.extracted_text = extracted_text
        context.metadata.ocr_method_used = self.settings.ocr_strategy.value

        self.logger.info(
            "OCR completed",
            page_count=len(images),
            text_length=len(extracted_text),
            ocr_method=self.settings.ocr_strategy.value,
        )

        context.set_stage_result(self.name, {
            "text_length": len(extracted_text),
            "ocr_method": self.settings.ocr_strategy.value,
        })

        return context
