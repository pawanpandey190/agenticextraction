"""Unit tests for utility functions."""

import io

import pytest
from PIL import Image

from financial_agent.utils.exceptions import (
    ClassificationError,
    CurrencyConversionError,
    DocumentLoadError,
    ExtractionError,
    FinancialAgentError,
    OCRError,
)
from financial_agent.utils.image_utils import (
    encode_image_base64,
    get_image_dimensions,
    image_to_bytes,
    resize_image_if_needed,
)


class TestExceptions:
    """Tests for custom exceptions."""

    def test_financial_agent_error(self):
        """Test base exception."""
        error = FinancialAgentError("Test error", {"key": "value"})
        assert error.message == "Test error"
        assert error.details == {"key": "value"}
        assert "Test error" in str(error)
        assert "key" in str(error)

    def test_document_load_error(self):
        """Test document load error."""
        error = DocumentLoadError("File not found")
        assert isinstance(error, FinancialAgentError)

    def test_ocr_error(self):
        """Test OCR error."""
        error = OCRError("OCR failed")
        assert isinstance(error, FinancialAgentError)

    def test_classification_error(self):
        """Test classification error."""
        error = ClassificationError("Classification failed")
        assert isinstance(error, FinancialAgentError)

    def test_extraction_error(self):
        """Test extraction error."""
        error = ExtractionError("Extraction failed")
        assert isinstance(error, FinancialAgentError)

    def test_currency_conversion_error(self):
        """Test currency conversion error."""
        error = CurrencyConversionError("Conversion failed")
        assert isinstance(error, FinancialAgentError)


class TestImageUtils:
    """Tests for image utilities."""

    @pytest.fixture
    def sample_image(self) -> Image.Image:
        """Create a sample test image."""
        return Image.new("RGB", (100, 100), color="white")

    @pytest.fixture
    def large_image(self) -> Image.Image:
        """Create a large test image."""
        return Image.new("RGB", (4000, 3000), color="white")

    def test_resize_image_small(self, sample_image: Image.Image):
        """Test resizing small image (no change needed)."""
        result = resize_image_if_needed(sample_image, max_dimension=2048)
        assert result.size == (100, 100)

    def test_resize_image_large(self, large_image: Image.Image):
        """Test resizing large image."""
        result = resize_image_if_needed(large_image, max_dimension=2048)
        assert result.width <= 2048
        assert result.height <= 2048

    def test_encode_image_base64_png(self, sample_image: Image.Image):
        """Test encoding image to base64 PNG."""
        base64_data, mime_type = encode_image_base64(sample_image, format="PNG")
        assert mime_type == "image/png"
        assert len(base64_data) > 0

    def test_encode_image_base64_jpeg(self, sample_image: Image.Image):
        """Test encoding image to base64 JPEG."""
        base64_data, mime_type = encode_image_base64(sample_image, format="JPEG")
        assert mime_type == "image/jpeg"
        assert len(base64_data) > 0

    def test_image_to_bytes(self, sample_image: Image.Image):
        """Test converting image to bytes."""
        image_bytes = image_to_bytes(sample_image, format="PNG")
        assert isinstance(image_bytes, bytes)
        assert len(image_bytes) > 0

    def test_get_image_dimensions(self, sample_image: Image.Image):
        """Test getting image dimensions."""
        image_bytes = image_to_bytes(sample_image)
        width, height = get_image_dimensions(image_bytes)
        assert width == 100
        assert height == 100

    def test_rgba_to_jpeg_conversion(self):
        """Test RGBA image conversion to JPEG."""
        rgba_image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        base64_data, mime_type = encode_image_base64(rgba_image, format="JPEG")
        assert mime_type == "image/jpeg"
        assert len(base64_data) > 0
