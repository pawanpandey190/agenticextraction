"""LLM Service for document classification using OpenAI vision."""

import base64
import json
from pathlib import Path

import structlog
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from master_orchestrator.config.settings import Settings
from master_orchestrator.config.constants import DocumentCategory
from master_orchestrator.models.input import ClassificationResult

logger = structlog.get_logger(__name__)

CLASSIFICATION_PROMPT = """Analyze this document image and classify it into one of the following categories:

1. PASSPORT - Identity documents such as passports, ID cards, or travel documents
2. FINANCIAL - Banking documents such as bank statements, balance certificates, bank letters, or financial statements
3. EDUCATION - Academic documents such as transcripts, degrees, diplomas, certificates, or mark sheets

Respond with ONLY a JSON object in this exact format:
{
    "category": "PASSPORT" | "FINANCIAL" | "EDUCATION",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}

If you cannot determine the category, respond with:
{
    "category": "UNKNOWN",
    "confidence": 0.0,
    "reasoning": "Explanation of why classification failed"
}
"""


class LLMService:
    """Service for LLM-based document classification."""

    def __init__(self, settings: Settings):
        """Initialize the LLM service.

        Args:
            settings: Application settings containing API key and model name
        """
        self._settings = settings
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = settings.model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def classify_document(self, file_path: Path) -> ClassificationResult:
        """Classify a document using OpenAI's vision capabilities.

        Args:
            file_path: Path to the document file

        Returns:
            ClassificationResult with category, confidence, and reasoning
        """
        logger.debug("classifying_document_with_llm", file=file_path.name)

        # Read and encode the image/PDF
        image_data, media_type = self._prepare_image(file_path)

        # Send to OpenAI for classification
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{image_data}",
                            },
                        },
                        {
                            "type": "text",
                            "text": CLASSIFICATION_PROMPT,
                        },
                    ],
                }
            ],
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        # Parse response
        return self._parse_classification_response(response)

    def _prepare_image(self, file_path: Path) -> tuple[str, str]:
        """Prepare image data for OpenAI API.

        For PDFs, converts first page to image.
        For images, reads directly.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (base64_data, media_type)
        """
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            # Convert PDF first page to image
            image_data, media_type = self._pdf_to_image(file_path)
        elif extension in {".png", ".jpg", ".jpeg"}:
            # Read image directly
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
            media_type = "image/png" if extension == ".png" else "image/jpeg"
        else:
            raise ValueError(f"Unsupported file type: {extension}")

        return image_data, media_type

    def _pdf_to_image(self, file_path: Path) -> tuple[str, str]:
        """Convert PDF first page to image.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (base64_data, media_type)
        """
        import io

        import pypdfium2 as pdfium
        from PIL import Image

        # Open PDF and render first page
        with pdfium.PdfDocument(str(file_path)) as pdf:
            page = pdf[0]
            # Render at 150 DPI for good quality while keeping size reasonable
            bitmap = page.render(scale=150 / 72)
            pil_image = bitmap.to_pil()

        # Convert to PNG bytes
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

        image_data = base64.standard_b64encode(img_bytes).decode("utf-8")
        return image_data, "image/png"

    def _parse_classification_response(self, response: object) -> ClassificationResult:
        """Parse OpenAI's classification response.

        Args:
            response: Response from OpenAI API

        Returns:
            ClassificationResult
        """
        try:
            # Extract text content from response
            content = response.choices[0].message.content

            data = json.loads(content)

            # Map category string to enum
            category_str = data.get("category", "UNKNOWN").upper()
            category = self._map_category(category_str)

            return ClassificationResult(
                category=category,
                confidence=float(data.get("confidence", 0.0)),
                method="llm",
                reasoning=data.get("reasoning", ""),
            )

        except (json.JSONDecodeError, KeyError, IndexError, AttributeError) as e:
            logger.warning("failed_to_parse_llm_response", error=str(e))
            return ClassificationResult(
                category=DocumentCategory.UNKNOWN,
                confidence=0.0,
                method="llm",
                reasoning=f"Failed to parse LLM response: {str(e)}",
            )

    def _map_category(self, category_str: str) -> DocumentCategory:
        """Map category string to DocumentCategory enum."""
        mapping = {
            "PASSPORT": DocumentCategory.PASSPORT,
            "FINANCIAL": DocumentCategory.FINANCIAL,
            "EDUCATION": DocumentCategory.EDUCATION,
        }
        return mapping.get(category_str, DocumentCategory.UNKNOWN)
