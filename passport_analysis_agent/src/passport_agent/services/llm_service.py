"""LLM service for OpenAI API interactions."""

import json
from typing import Any, TypeVar

from openai import OpenAI
import structlog
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config.settings import Settings
from ..utils.exceptions import LLMError

logger = structlog.get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Service for interacting with OpenAI API."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the LLM service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value()
        )
        self.model = settings.llm_model
        self.max_tokens = settings.llm_max_tokens
        self.temperature = settings.llm_temperature

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def extract_from_image(
        self,
        image_base64: str,
        mime_type: str,
        system_prompt: str,
        extraction_prompt: str,
    ) -> str:
        """Extract information from an image using OpenAI Vision.

        Args:
            image_base64: Base64 encoded image
            mime_type: MIME type of the image
            system_prompt: System prompt for the model
            extraction_prompt: User prompt for extraction

        Returns:
            Extracted text response

        Raises:
            LLMError: If extraction fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}",
                                },
                            },
                            {
                                "type": "text",
                                "text": extraction_prompt,
                            },
                        ],
                    }
                ],
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error("OpenAI API error during extraction", error=str(e))
            raise LLMError(f"Failed to extract from image: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def extract_with_structured_output(
        self,
        image_base64: str,
        mime_type: str,
        system_prompt: str,
        response_model: type[T],
    ) -> T:
        """Extract structured data from an image.

        Args:
            image_base64: Base64 encoded image
            mime_type: MIME type of the image
            system_prompt: System prompt for the model
            response_model: Pydantic model for the response

        Returns:
            Parsed response model

        Raises:
            LLMError: If extraction fails
        """
        # Build the JSON schema from the Pydantic model
        schema = response_model.model_json_schema()

        extraction_prompt = f"""Analyze this passport image and extract the requested information.

Return ONLY valid JSON that matches this schema. Do not include any other text, markdown formatting, or code blocks.

JSON Schema:
{json.dumps(schema, indent=2)}

Extract all visible passport data from the image. If a field is not visible or unclear, use null."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}",
                                },
                            },
                            {
                                "type": "text",
                                "text": extraction_prompt,
                            },
                        ],
                    }
                ],
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content or ""

            # Try to extract JSON from the response
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)

            return response_model.model_validate(data)

        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse JSON response",
                error=str(e),
                response=response_text[:500] if 'response_text' in locals() else "N/A",
            )
            raise LLMError(f"Failed to parse structured response: {e}") from e
        except Exception as e:
            logger.error("OpenAI API error during structured extraction", error=str(e))
            raise LLMError(f"Failed to extract structured data: {e}") from e

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
