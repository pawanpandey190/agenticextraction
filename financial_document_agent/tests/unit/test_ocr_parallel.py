"""Unit tests for parallel OCR processing."""

import os
from unittest.mock import MagicMock, patch, call
from io import BytesIO

import pytest
from PIL import Image

from financial_agent.config.settings import Settings
from financial_agent.services.ocr_service import OpenAIVisionOCR, create_ocr_service
from financial_agent.utils.exceptions import OCRError


def create_test_image() -> tuple[bytes, str]:
    """Create a test image for OCR testing."""
    img = Image.new("RGB", (100, 100), color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.read(), "image/png"


class TestOpenAIVisionOCRParallel:
    """Tests for parallel OCR processing in OpenAIVisionOCR."""

    @pytest.fixture
    def mock_llm_service(self):
        """Create a mock LLM service."""
        mock = MagicMock()
        mock.extract_text_from_image.side_effect = lambda *args, **kwargs: "Extracted text"
        return mock

    def test_single_page_no_parallelization(self, mock_llm_service):
        """Test that single page doesn't use parallelization."""
        ocr = OpenAIVisionOCR(mock_llm_service, max_workers=4)
        images = [create_test_image()]

        result = ocr.extract_text_from_multiple(images)

        assert "--- Page 1 ---" in result
        assert "Extracted text" in result
        assert mock_llm_service.extract_text_from_image.call_count == 1

    def test_multiple_pages_parallel(self, mock_llm_service):
        """Test that multiple pages are processed in parallel."""
        ocr = OpenAIVisionOCR(mock_llm_service, max_workers=4)
        images = [create_test_image() for _ in range(5)]

        result = ocr.extract_text_from_multiple(images)

        # All pages should be present
        for i in range(1, 6):
            assert f"--- Page {i} ---" in result

        assert mock_llm_service.extract_text_from_image.call_count == 5

    def test_page_order_preserved(self, mock_llm_service):
        """Test that page order is preserved in results."""
        # Return different text for each call to verify order
        call_order = []

        def side_effect(*args, **kwargs):
            idx = len(call_order)
            call_order.append(idx)
            return f"Text from page {idx + 1}"

        mock_llm_service.extract_text_from_image.side_effect = side_effect

        ocr = OpenAIVisionOCR(mock_llm_service, max_workers=4)
        images = [create_test_image() for _ in range(10)]

        result = ocr.extract_text_from_multiple(images)

        # Pages should be in order in the result
        page_positions = []
        for i in range(1, 11):
            pos = result.find(f"--- Page {i} ---")
            assert pos != -1, f"Page {i} not found in result"
            page_positions.append(pos)

        # Verify pages are in ascending order
        assert page_positions == sorted(page_positions)

    def test_partial_failure_handling(self, mock_llm_service):
        """Test that partial failures don't block other pages."""
        call_count = [0]

        def side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:
                raise OCRError("Simulated failure")
            return f"Text from call {call_count[0]}"

        mock_llm_service.extract_text_from_image.side_effect = side_effect

        ocr = OpenAIVisionOCR(mock_llm_service, max_workers=4)
        images = [create_test_image() for _ in range(5)]

        result = ocr.extract_text_from_multiple(images)

        # Should have all pages, with one marked as failed
        assert "[OCR FAILED]" in result
        # Other pages should have content
        successful_count = result.count("Text from call")
        assert successful_count == 4  # 5 - 1 failed

    def test_empty_images_list(self, mock_llm_service):
        """Test handling of empty images list."""
        ocr = OpenAIVisionOCR(mock_llm_service, max_workers=4)

        result = ocr.extract_text_from_multiple([])

        assert result == ""
        assert mock_llm_service.extract_text_from_image.call_count == 0

    def test_max_workers_respected(self, mock_llm_service):
        """Test that max_workers parameter is stored correctly."""
        ocr_2 = OpenAIVisionOCR(mock_llm_service, max_workers=2)
        ocr_8 = OpenAIVisionOCR(mock_llm_service, max_workers=8)

        assert ocr_2.max_workers == 2
        assert ocr_8.max_workers == 8

    def test_extract_single_page_success(self):
        """Test _extract_single_page helper method on success."""
        mock_llm = MagicMock()
        mock_llm.extract_text_from_image.return_value = "Success text"
        ocr = OpenAIVisionOCR(mock_llm, max_workers=4)
        image_bytes, mime_type = create_test_image()

        page_index, text = ocr._extract_single_page(1, image_bytes, mime_type)

        assert page_index == 1
        assert text == "Success text"

    def test_extract_single_page_failure(self, mock_llm_service):
        """Test _extract_single_page helper method on failure."""
        mock_llm_service.extract_text_from_image.side_effect = OCRError("Test error")
        ocr = OpenAIVisionOCR(mock_llm_service, max_workers=4)
        image_bytes, mime_type = create_test_image()

        page_index, text = ocr._extract_single_page(1, image_bytes, mime_type)

        assert page_index == 1
        assert text == "[OCR FAILED]"


class TestCreateOCRService:
    """Tests for OCR service factory function."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        with patch.dict(os.environ, {
            "FA_OPENAI_API_KEY": "test-api-key",
            "FA_LLM_MODEL": "gpt-4o",
            "FA_OCR_MAX_WORKERS": "6",
        }):
            return Settings()

    def test_factory_passes_max_workers(self, mock_settings):
        """Test that factory function passes max_workers to OCR service."""
        with patch("financial_agent.services.ocr_service.LLMService"):
            service = create_ocr_service(mock_settings)

        assert hasattr(service, "max_workers")
        assert service.max_workers == 6

    def test_factory_default_max_workers(self):
        """Test that factory uses default max_workers from settings."""
        with patch.dict(os.environ, {
            "FA_OPENAI_API_KEY": "test-api-key",
            "FA_LLM_MODEL": "gpt-4o",
        }):
            settings = Settings()

        with patch("financial_agent.services.ocr_service.LLMService"):
            service = create_ocr_service(settings)

        assert service.max_workers == 4  # Default value
