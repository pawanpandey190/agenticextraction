"""Unit tests for services."""

import os
from unittest.mock import MagicMock, patch

import pytest

from financial_agent.config.constants import FALLBACK_EXCHANGE_RATES
from financial_agent.config.settings import Settings
from financial_agent.services.exchange_service import ExchangeRateCache, ExchangeService
from financial_agent.utils.exceptions import CurrencyConversionError


class TestExchangeRateCache:
    """Tests for ExchangeRateCache."""

    def test_set_and_get(self):
        """Test setting and getting cached rates."""
        cache = ExchangeRateCache(ttl_seconds=3600)
        rates = {"EUR": 1.0, "GBP": 0.86}

        cache.set("USD", rates)
        result = cache.get("USD")

        assert result == rates

    def test_get_missing(self):
        """Test getting non-existent entry."""
        cache = ExchangeRateCache(ttl_seconds=3600)
        assert cache.get("USD") is None

    def test_expiration(self):
        """Test cache expiration."""
        import time

        cache = ExchangeRateCache(ttl_seconds=1)
        cache.set("USD", {"EUR": 1.0})

        # Should exist initially
        assert cache.get("USD") is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("USD") is None

    def test_clear(self):
        """Test clearing cache."""
        cache = ExchangeRateCache(ttl_seconds=3600)
        cache.set("USD", {"EUR": 1.0})
        cache.set("GBP", {"EUR": 1.0})

        cache.clear()

        assert cache.get("USD") is None
        assert cache.get("GBP") is None


class TestExchangeService:
    """Tests for ExchangeService."""

    @pytest.fixture
    def exchange_service(self, mock_settings: Settings) -> ExchangeService:
        """Create exchange service for testing."""
        return ExchangeService(mock_settings)

    def test_same_currency(self, exchange_service: ExchangeService):
        """Test conversion with same currency."""
        rate = exchange_service.get_rate("EUR", "EUR")
        assert rate == 1.0

    def test_fallback_rate(self, exchange_service: ExchangeService):
        """Test fallback rates when API fails."""
        with patch.object(exchange_service, "_fetch_rates", side_effect=CurrencyConversionError("API error")):
            rate = exchange_service._get_fallback_rate("USD", "EUR")

            # Should use fallback rate
            expected = 1.0 / FALLBACK_EXCHANGE_RATES["USD"]
            assert abs(rate - expected) < 0.01

    def test_convert(self, exchange_service: ExchangeService):
        """Test currency conversion."""
        with patch.object(exchange_service, "get_rate", return_value=0.92):
            amount, rate = exchange_service.convert(100.0, "USD", "EUR")

            assert rate == 0.92
            assert amount == 92.0

    def test_fallback_unknown_currency(self, exchange_service: ExchangeService):
        """Test fallback with unknown currency."""
        with pytest.raises(CurrencyConversionError):
            exchange_service._get_fallback_rate("XYZ", "EUR")


class TestLLMService:
    """Tests for LLMService."""

    def test_extract_json_from_code_block(self, mock_settings: Settings):
        """Test extracting JSON from code block."""
        from financial_agent.services.llm_service import LLMService

        with patch("anthropic.Anthropic"):
            service = LLMService(mock_settings)

        text = '```json\n{"key": "value"}\n```'
        result = service._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_json_plain(self, mock_settings: Settings):
        """Test extracting plain JSON."""
        from financial_agent.services.llm_service import LLMService

        with patch("anthropic.Anthropic"):
            service = LLMService(mock_settings)

        text = 'Here is the result: {"key": "value"}'
        result = service._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_json_nested(self, mock_settings: Settings):
        """Test extracting nested JSON."""
        from financial_agent.services.llm_service import LLMService

        with patch("anthropic.Anthropic"):
            service = LLMService(mock_settings)

        text = '{"outer": {"inner": "value"}}'
        result = service._extract_json(text)
        assert '"outer"' in result
        assert '"inner"' in result
