"""OCR processing stage using Claude Vision."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from ...config.settings import Settings
from ...prompts.system import OCR_SYSTEM_PROMPT
from ...services.llm_service import LLMService
from ...utils.exceptions import OCRError
from ...utils.image_utils import bytes_to_image, encode_image_base64, resize_image_if_needed
from ..base import PipelineContext, PipelineStage


class OCRProcessorStage(PipelineStage):
    """Stage for extracting text from documents using Claude Vision."""

    def __init__(self, settings: Settings, llm_service: LLMService | None = None) -> None:
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)
        self.max_workers = settings.ocr_max_workers

    @property
    def name(self) -> str:
        return "ocr_processor"

    def _extract_page_text(
        self,
        page_data: bytes,
        page_number: int,
        total_pages: int,
    ) -> tuple[int, str]:
        """Extract text from a single page.

        Args:
            page_data: Raw image bytes for the page
            page_number: Page number (1-indexed)
            total_pages: Total number of pages in document

        Returns:
            Tuple of (page_number, extracted_text)
        """
        try:
            img = bytes_to_image(page_data)
            img = resize_image_if_needed(img)
            base64_data, mime_type = encode_image_base64(img)

            text = self.llm_service.extract_text_from_image(
                image_base64=base64_data,
                mime_type=mime_type,
                prompt=self._get_ocr_prompt(page_number, total_pages),
            )
            return (page_number, text)
        except Exception as e:
            self.logger.warning(
                "Failed to extract text from page",
                page_number=page_number,
                error=str(e),
            )
            return (page_number, "[OCR FAILED]")

    def process(self, context: PipelineContext) -> PipelineContext:
        """Extract text from all documents using parallel processing.

        Args:
            context: Pipeline context

        Returns:
            Updated context with extracted texts

        Raises:
            OCRError: If OCR processing fails critically
        """
        if not context.documents:
            raise OCRError("No documents loaded for OCR processing")

        successful_extractions = 0

        # Collect all pages across all documents for parallel processing
        all_pages: list[tuple[str, int, int, bytes]] = []
        for document in context.documents:
            file_path = str(document.file_path)
            for page in document.pages:
                all_pages.append((
                    file_path,
                    page.page_number,
                    document.page_count,
                    page.image_data,
                ))

        # Process all pages in parallel
        page_results: dict[str, dict[int, str]] = {}
        for document in context.documents:
            page_results[str(document.file_path)] = {}

        if all_pages:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(
                        self._extract_page_text,
                        page_data,
                        page_number,
                        total_pages,
                    ): (file_path, page_number)
                    for file_path, page_number, total_pages, page_data in all_pages
                }

                for future in as_completed(futures):
                    file_path, page_number = futures[future]
                    extracted_page_number, text = future.result()
                    page_results[file_path][extracted_page_number] = text

            self.logger.info(
                "Parallel OCR completed",
                total_pages=len(all_pages),
                max_workers=self.max_workers,
            )

        # Reconstruct per-document results
        for document in context.documents:
            file_path = str(document.file_path)
            doc_page_results = page_results.get(file_path, {})

            if doc_page_results:
                page_texts = []
                for page_num in range(1, document.page_count + 1):
                    text = doc_page_results.get(page_num, "[OCR FAILED]")
                    page_texts.append(f"--- Page {page_num} ---\n{text}")

                full_text = "\n\n".join(page_texts)
                context.add_extracted_text(file_path, full_text)

                # Check if any page failed
                if "[OCR FAILED]" not in full_text:
                    successful_extractions += 1
                else:
                    context.metadata.add_error(f"Some pages failed OCR for {file_path}")

                self.logger.info(
                    "Text extracted from document",
                    file_path=file_path,
                    pages=document.page_count,
                    text_length=len(full_text),
                )
            else:
                context.metadata.add_error(f"OCR failed for {file_path}")
                context.add_extracted_text(file_path, "")

        context.metadata.ocr_method_used = "claude_vision"

        self.logger.info(
            "OCR processing completed",
            total_documents=len(context.documents),
            successful_extractions=successful_extractions,
        )

        context.set_stage_result(self.name, {
            "total_documents": len(context.documents),
            "successful_extractions": successful_extractions,
            "method": "claude_vision",
        })

        return context

    def _get_ocr_prompt(self, page_number: int, total_pages: int) -> str:
        """Get the OCR prompt for a specific page.

        Args:
            page_number: Current page number
            total_pages: Total number of pages

        Returns:
            OCR prompt string
        """
        base_prompt = (
            "Extract all text from this education document image. "
            "Preserve the structure and formatting as much as possible. "
            "Include all names, dates, grades, marks, percentages, and credential information. "
            "If there are tables, represent them in a clear format. "
            "Pay special attention to: institution names, qualification names, grades/marks, "
            "semester numbers, student names, and dates."
        )

        if total_pages > 1:
            base_prompt += f"\n\nThis is page {page_number} of {total_pages}."

        return base_prompt
