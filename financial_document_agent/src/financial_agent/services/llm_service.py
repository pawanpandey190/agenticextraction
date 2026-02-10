"""LLM service for Anthropic Claude API interactions."""

import json
from typing import Any, TypeVar

from anthropic import Anthropic
import structlog
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config.settings import Settings
from ..utils.exceptions import LLMError
from .cache import LLMCache

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Service for interacting with Anthropic Claude API."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the LLM service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        import os
        # Bypass Pydantic settings and use os.environ directly like test.py
        api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
 
        self.client = Anthropic(api_key=api_key)
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

        # Initialize cache if enabled
        self._cache: LLMCache | None = None
        if settings.enable_llm_cache:
            self._cache = LLMCache(
                max_size=settings.llm_cache_max_size,
                ttl_seconds=settings.llm_cache_ttl_minutes * 60,
            )
            logger.info(
                "LLM cache enabled",
                max_size=settings.llm_cache_max_size,
                ttl_minutes=settings.llm_cache_ttl_minutes,
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def extract_text_from_image(
        self,
        image_base64: str,
        mime_type: str,
        prompt: str | None = None,
        image_bytes: bytes | None = None,
    ) -> str:
        """Extract text from an image using Anthropic Claude Vision.

        Args:
            image_base64: Base64 encoded image
            mime_type: MIME type of the image
            prompt: Optional custom prompt for extraction
            image_bytes: Optional raw image bytes for cache key generation

        Returns:
            Extracted text

        Raises:
            LLMError: If extraction fails
        """
        if prompt is None:
            prompt = (
                "Extract all text from this financial document image. "
                "Preserve the structure and formatting as much as possible. "
                "Include all numbers, dates, account information, and amounts. "
                "If there are tables, represent them in a clear format."
            )

        # Check cache if enabled and image_bytes provided
        cache_key: str | None = None
        if self._cache is not None and image_bytes is not None:
            cache_key = LLMCache.generate_key(image_bytes, self.model, prompt)
            cached_result = self._cache.get(cache_key)
            if cached_result is not None:
                logger.debug("Using cached OCR result")
                return cached_result

        try:
            # Anthropic vision format
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            result = response.content[0].text if response.content else ""

            # Store in cache if enabled
            if self._cache is not None and cache_key is not None:
                self._cache.set(cache_key, result)

            return result

        except Exception as e:
            logger.error("Anthropic API error during text extraction", error=str(e))
            raise LLMError(f"Failed to extract text from image: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def analyze_with_structured_output(
        self,
        content: str | list[dict[str, Any]],
        system_prompt: str,
        response_model: type[T],
    ) -> T:
        """Analyze content and return structured output.

        Args:
            content: Text content or list of content blocks (for images)
            system_prompt: System prompt for the analysis
            response_model: Pydantic model for the response

        Returns:
            Parsed response model

        Raises:
            LLMError: If analysis fails
        """
        # Build the JSON schema from the Pydantic model
        schema = response_model.model_json_schema()

        extraction_prompt = f"""
Analyze the provided content and extract information according to this JSON schema:

{json.dumps(schema, indent=2)}

Return ONLY valid JSON that matches this schema. Do not include any other text or explanation.
"""

        # Build messages content
        user_content = []
        if isinstance(content, str):
            user_content.append({"type": "text", "text": content})
        else:
            for block in content:
                if block["type"] == "image":
                    source = block["source"]
                    user_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": source['media_type'],
                            "data": source['data'],
                        },
                    })
                else:
                    user_content.append(block)
        
        user_content.append({"type": "text", "text": extraction_prompt})

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_content}
                ],
            )

            response_text = response.content[0].text if response.content else ""

            # Try to extract JSON from the response
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)

            return response_model.model_validate(data)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response", error=str(e), response=response_text if 'response_text' in locals() else "N/A")
            raise LLMError(f"Failed to parse structured response: {e}") from e
        except Exception as e:
            logger.error("Anthropic API error during analysis", error=str(e))
            raise LLMError(f"Failed to analyze content: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def classify_document(
        self,
        text: str,
        image_base64: str | None = None,
        mime_type: str | None = None,
        system_prompt: str = "",
        classification_prompt: str = "",
    ) -> dict[str, Any]:
        """Classify a document based on its content.

        Args:
            text: Extracted text from the document
            image_base64: Optional base64 encoded image
            mime_type: MIME type if image provided
            system_prompt: System prompt
            classification_prompt: Classification instructions

        Returns:
            Classification result as dict

        Raises:
            LLMError: If classification fails
        """
        user_content = []

        if image_base64 and mime_type:
            user_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": mime_type,
                    "data": image_base64,
                },
            })

        user_content.append({
            "type": "text",
            "text": f"Document text:\n\n{text}\n\n{classification_prompt}",
        })

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_content}
                ],
            )

            response_text = response.content[0].text if response.content else ""
            json_str = self._extract_json(response_text)

            return json.loads(json_str)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse classification response", error=str(e))
            raise LLMError(f"Failed to parse classification: {e}") from e
        except Exception as e:
            logger.error("Anthropic API error during classification", error=str(e))
            raise LLMError(f"Failed to classify document: {e}") from e

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
