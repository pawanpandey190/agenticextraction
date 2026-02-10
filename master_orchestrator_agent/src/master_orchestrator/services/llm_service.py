"""LLM Service for document classification using Anthropic Claude vision."""

import base64
import json
from pathlib import Path
from typing import Any
import io

import structlog
from anthropic import Anthropic
from PIL import Image
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
        import os
        # Bypass Pydantic settings and use os.environ directly like test.py
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
        
        self._client = Anthropic(api_key=api_key)
        # Diagnostic
        key_preview = f"{api_key[:12]}...{api_key[-5:]}" if api_key else "EMPTY"
        logger.error("MASTER_LLM_DIAGNOSTIC", key_preview=key_preview, model=settings.model_name)
        self._model = settings.model_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def classify_document(self, file_path: Path) -> ClassificationResult:
        """Classify a document using Anthropic's vision capabilities.

        Args:
            file_path: Path to the document file

        Returns:
            ClassificationResult with category, confidence, and reasoning
        """
        logger.debug("classifying_document_with_llm", file=file_path.name)

        # Read and encode the image/PDF
        image_data, media_type = self._prepare_image(file_path)

        # Send to Anthropic for classification
        response = self._client.messages.create(
            model=self._model,
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": CLASSIFICATION_PROMPT,
                        },
                    ],
                }
            ],
        )

        # Parse response
        return self._parse_classification_response(response)

    def _prepare_image(self, file_path: Path) -> tuple[str, str]:
        """Prepare image data for Anthropic API with size optimization.

        For PDFs, converts first page to image.
        For images, reads directly and optimizes.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (base64_data, media_type)
        """
        extension = file_path.suffix.lower()

        if extension == ".pdf":
            # Convert PDF first page to image
            return self._pdf_to_image(file_path)
        elif extension in {".png", ".jpg", ".jpeg"}:
            # Read image and optimize
            img = Image.open(file_path)
            return self._encode_and_optimize(img)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    def _pdf_to_image(self, file_path: Path) -> tuple[str, str]:
        """Convert PDF first page to image and optimize.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple of (base64_data, media_type)
        """
        import pypdfium2 as pdfium

        # Open PDF and render first page
        with pdfium.PdfDocument(str(file_path)) as pdf:
            page = pdf[0]
            # Render at 150 DPI for good quality
            bitmap = page.render(scale=150 / 72)
            pil_image = bitmap.to_pil()

        return self._encode_and_optimize(pil_image)

    def _encode_and_optimize(self, image: Image.Image, max_size: int = 3072 * 1024) -> tuple[str, str]:
        """Encode image to base64 with size optimization. Target 3.0MB raw (approx 4.0MB base64)."""
        # 1. Resize if too large (Claude limit)
        MAX_DIM = 2048
        w, h = image.size
        print(f"DEBUG_MASTER: Optimizing image {w}x{h}")
        if w > MAX_DIM or h > MAX_DIM:
            scale = min(MAX_DIM / w, MAX_DIM / h)
            image = image.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
            print(f"DEBUG_MASTER: Resized to {image.size} (limit: {MAX_DIM})")

        # 2. Convert RGBA to RGB for JPEG
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # 3. Save as JPEG with quality reduction loop
        quality = 85
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality)
        
        while buffer.tell() > max_size and quality > 30:
            quality -= 10
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=quality)
            print(f"DEBUG_MASTER: Quality reduction -> {quality}, size: {buffer.tell()} bytes")

        # 4. Final resize fallback if still too large (Looping)
        if buffer.tell() > max_size:
            while buffer.tell() > max_size:
                # Reduce dimensions by 20% each step
                w, h = image.size
                if w < 100 or h < 100: break # Safety break
                image = image.resize((int(w * 0.8), int(h * 0.8)), Image.Resampling.LANCZOS)
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=70)
                print(f"DEBUG_MASTER: Iterative resize -> {image.size}, size: {buffer.tell()} bytes")

        image_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")
        print(f"DEBUG_MASTER: Final base64 size approx: {len(image_data)} bytes")
        return image_data, "image/jpeg"

    def _parse_classification_response(self, response: Any) -> ClassificationResult:
        """Parse Anthropic's classification response.

        Args:
            response: Response from Anthropic API

        Returns:
            ClassificationResult
        """
        try:
            # Extract text content from response
            content = response.content[0].text if response.content else ""

            # Try to extract JSON from the response
            json_str = self._extract_json(content)
            data = json.loads(json_str)

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

    def _extract_json(self, text: str) -> str:
        """Extract JSON from a text response.

        Args:
            text: Response text that may contain JSON

        Returns:
            Extracted JSON string
        """
        # Try to find JSON in code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end > start:
                return text[start:end].strip()

        # Try to find JSON object or array
        for start_char, end_char in [("{", "}"), ("[", "]")]:
            start = text.find(start_char)
            if start != -1:
                # Find matching end
                depth = 0
                for i, char in enumerate(text[start:], start):
                    if char == start_char:
                        depth += 1
                    elif char == end_char:
                        depth -= 1
                        if depth == 0:
                            return text[start : i + 1]

        # Return as-is if no JSON found
        return text.strip()
