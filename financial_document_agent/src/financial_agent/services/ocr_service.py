"""OCR service abstraction with multiple backends."""

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

import structlog

from ..config.constants import OCRStrategy
from ..config.settings import Settings
from ..utils.exceptions import OCRError
from ..utils.image_utils import encode_image_base64, bytes_to_image, resize_image_if_needed
from .llm_service import LLMService

logger = structlog.get_logger(__name__)


class OCRService(ABC):
    """Abstract base class for OCR services."""

    @abstractmethod
    def extract_text(self, image_bytes: bytes, mime_type: str) -> str:
        """Extract text from an image.

        Args:
            image_bytes: Raw image bytes
            mime_type: MIME type of the image

        Returns:
            Extracted text

        Raises:
            OCRError: If text extraction fails
        """
        pass

    @abstractmethod
    def extract_text_from_multiple(
        self,
        images: list[tuple[bytes, str]],
    ) -> str:
        """Extract text from multiple images.

        Args:
            images: List of (image_bytes, mime_type) tuples

        Returns:
            Combined extracted text

        Raises:
            OCRError: If text extraction fails
        """
        pass


class AnthropicVisionOCR(OCRService):
    """OCR implementation using Anthropic Claude Vision API."""

    def __init__(self, llm_service: LLMService, max_workers: int = 4) -> None:
        """Initialize Anthropic Vision OCR.

        Args:
            llm_service: LLM service instance
            max_workers: Maximum concurrent OCR API calls
        """
        self.llm_service = llm_service
        self.max_workers = max_workers

    def extract_text(self, image_bytes: bytes, mime_type: str) -> str:
        """Extract text using Anthropic Claude Vision.

        Args:
            image_bytes: Raw image bytes
            mime_type: MIME type of the image

        Returns:
            Extracted text

        Raises:
            OCRError: If extraction fails
        """
        try:
            # Resize image if needed
            image = bytes_to_image(image_bytes)
            image = resize_image_if_needed(image)

            # Encode to base64 with size management
            base64_data, actual_mime = encode_image_base64(image)

            text = self.llm_service.extract_text_from_image(
                base64_data, actual_mime, image_bytes=image_bytes
            )
            logger.debug("Anthropic Vision OCR completed", text_length=len(text))

            return text

        except Exception as e:
            logger.error("Anthropic Vision OCR failed", error=str(e))
            raise OCRError(f"Anthropic Vision OCR failed: {e}") from e

    def _extract_single_page(
        self,
        page_index: int,
        image_bytes: bytes,
        mime_type: str,
    ) -> tuple[int, str]:
        """Extract text from a single page.

        Args:
            page_index: 1-based page index
            image_bytes: Raw image bytes
            mime_type: MIME type of the image

        Returns:
            Tuple of (page_index, extracted_text)
        """
        try:
            text = self.extract_text(image_bytes, mime_type)
            return (page_index, text)
        except OCRError as e:
            logger.warning(f"Failed to extract text from page {page_index}", error=str(e))
            return (page_index, "[OCR FAILED]")

    def extract_text_from_multiple(
        self,
        images: list[tuple[bytes, str]],
    ) -> str:
        """Extract text from multiple images in parallel.

        Args:
            images: List of (image_bytes, mime_type) tuples

        Returns:
            Combined extracted text with page separators

        Raises:
            OCRError: If extraction fails
        """
        if not images:
            return ""

        # For single image, no need for parallelization
        if len(images) == 1:
            image_bytes, mime_type = images[0]
            try:
                text = self.extract_text(image_bytes, mime_type)
                return f"--- Page 1 ---\n{text}"
            except OCRError as e:
                logger.warning("Failed to extract text from page 1", error=str(e))
                return "--- Page 1 ---\n[OCR FAILED]"

        # Process pages in parallel
        results: dict[int, str] = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    self._extract_single_page, i, image_bytes, mime_type
                ): i
                for i, (image_bytes, mime_type) in enumerate(images, 1)
            }

            for future in as_completed(futures):
                page_index, text = future.result()
                results[page_index] = text

        # Combine results in page order
        texts = []
        for i in range(1, len(images) + 1):
            texts.append(f"--- Page {i} ---\n{results[i]}")

        logger.info(
            "Parallel OCR completed",
            total_pages=len(images),
            max_workers=self.max_workers,
        )

        return "\n\n".join(texts)


class TesseractOCR(OCRService):
    """OCR implementation using Tesseract (fallback)."""

    def __init__(self) -> None:
        """Initialize Tesseract OCR."""
        try:
            import pytesseract

            self.pytesseract = pytesseract
        except ImportError:
            raise OCRError(
                "pytesseract is not installed. "
                "Install with: pip install pytesseract"
            )

    def extract_text(self, image_bytes: bytes, mime_type: str) -> str:
        """Extract text using Tesseract.

        Args:
            image_bytes: Raw image bytes
            mime_type: MIME type of the image

        Returns:
            Extracted text

        Raises:
            OCRError: If extraction fails
        """
        try:
            image = bytes_to_image(image_bytes)
            text = self.pytesseract.image_to_string(image)
            logger.debug("Tesseract OCR completed", text_length=len(text))
            return text

        except Exception as e:
            logger.error("Tesseract OCR failed", error=str(e))
            raise OCRError(f"Tesseract OCR failed: {e}") from e

    def extract_text_from_multiple(
        self,
        images: list[tuple[bytes, str]],
    ) -> str:
        """Extract text from multiple images.

        Args:
            images: List of (image_bytes, mime_type) tuples

        Returns:
            Combined extracted text with page separators

        Raises:
            OCRError: If extraction fails
        """
        texts = []

        for i, (image_bytes, mime_type) in enumerate(images, 1):
            try:
                text = self.extract_text(image_bytes, mime_type)
                texts.append(f"--- Page {i} ---\n{text}")
            except OCRError as e:
                logger.warning(f"Failed to extract text from page {i}", error=str(e))
                texts.append(f"--- Page {i} ---\n[OCR FAILED]")

        return "\n\n".join(texts)


class AutoOCR(OCRService):
    """OCR service that tries Anthropic Claude Vision first, then falls back to Tesseract."""

    def __init__(self, llm_service: LLMService, max_workers: int = 4) -> None:
        """Initialize Auto OCR.

        Args:
            llm_service: LLM service for Claude Vision
            max_workers: Maximum concurrent OCR API calls
        """
        self.anthropic_ocr = AnthropicVisionOCR(llm_service, max_workers=max_workers)
        self._tesseract_ocr: TesseractOCR | None = None

    @property
    def tesseract_ocr(self) -> TesseractOCR | None:
        """Lazy initialize Tesseract OCR."""
        if self._tesseract_ocr is None:
            try:
                self._tesseract_ocr = TesseractOCR()
            except OCRError:
                logger.warning("Tesseract not available for fallback")
        return self._tesseract_ocr

    def extract_text(self, image_bytes: bytes, mime_type: str) -> str:
        """Extract text, trying Anthropic Claude Vision first.

        Args:
            image_bytes: Raw image bytes
            mime_type: MIME type of the image

        Returns:
            Extracted text

        Raises:
            OCRError: If all OCR methods fail
        """
        try:
            return self.anthropic_ocr.extract_text(image_bytes, mime_type)
        except OCRError as anthropic_error:
            logger.warning("Anthropic Claude Vision failed, trying Tesseract", error=str(anthropic_error))

            if self.tesseract_ocr:
                try:
                    return self.tesseract_ocr.extract_text(image_bytes, mime_type)
                except OCRError as tesseract_error:
                    raise OCRError(
                        f"All OCR methods failed. Anthropic: {anthropic_error}, Tesseract: {tesseract_error}"
                    )

            raise OCRError(f"Anthropic Claude Vision failed and Tesseract not available: {anthropic_error}")

    def extract_text_from_multiple(
        self,
        images: list[tuple[bytes, str]],
    ) -> str:
        """Extract text from multiple images.

        Args:
            images: List of (image_bytes, mime_type) tuples

        Returns:
            Combined extracted text

        Raises:
            OCRError: If extraction fails
        """
        try:
            return self.anthropic_ocr.extract_text_from_multiple(images)
        except OCRError as anthropic_error:
            logger.warning("Anthropic Claude Vision failed for batch, trying Tesseract")

            if self.tesseract_ocr:
                try:
                    return self.tesseract_ocr.extract_text_from_multiple(images)
                except OCRError as tesseract_error:
                    raise OCRError(
                        f"All OCR methods failed for batch. Anthropic: {anthropic_error}, Tesseract: {tesseract_error}"
                    )

            raise


def create_ocr_service(
    settings: Settings,
    llm_service: LLMService | None = None,
) -> OCRService:
    """Factory function to create an OCR service based on settings.

    Args:
        settings: Application settings
        llm_service: LLM service (required for Claude Vision)

    Returns:
        OCR service instance

    Raises:
        OCRError: If required dependencies are missing
    """
    strategy = settings.ocr_strategy
    max_workers = settings.ocr_max_workers

    if strategy == OCRStrategy.TESSERACT:
        return TesseractOCR()

    if llm_service is None:
        llm_service = LLMService(settings)

    if strategy == OCRStrategy.ANTHROPIC_VISION:
        return AnthropicVisionOCR(llm_service, max_workers=max_workers)

    # Auto strategy
    return AutoOCR(llm_service, max_workers=max_workers)
