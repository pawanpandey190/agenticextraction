"""Exchange rate service using Frankfurter API."""

import time
from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config.constants import DEFAULT_TARGET_CURRENCY, FALLBACK_EXCHANGE_RATES
from ..config.settings import Settings
from ..utils.exceptions import CurrencyConversionError

logger = structlog.get_logger(__name__)


class ExchangeRateCache:
    """Simple in-memory cache for exchange rates."""

    def __init__(self, ttl_seconds: int) -> None:
        """Initialize the cache.

        Args:
            ttl_seconds: Time-to-live for cached entries
        """
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[float, dict[str, float]]] = {}

    def get(self, base_currency: str) -> dict[str, float] | None:
        """Get cached rates for a base currency.

        Args:
            base_currency: Base currency code

        Returns:
            Cached rates or None if expired/not found
        """
        if base_currency not in self._cache:
            return None

        timestamp, rates = self._cache[base_currency]
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[base_currency]
            return None

        return rates

    def set(self, base_currency: str, rates: dict[str, float]) -> None:
        """Cache rates for a base currency.

        Args:
            base_currency: Base currency code
            rates: Exchange rates
        """
        self._cache[base_currency] = (time.time(), rates)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()


class ExchangeService:
    """Service for fetching and caching exchange rates."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the exchange service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.api_url = settings.exchange_api_url
        self.cache = ExchangeRateCache(settings.exchange_cache_ttl_seconds)
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            self._client.close()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    def _fetch_rates(self, base_currency: str) -> dict[str, float]:
        """Fetch exchange rates from the API.

        Args:
            base_currency: Base currency code

        Returns:
            Dictionary of currency codes to rates

        Raises:
            CurrencyConversionError: If fetch fails
        """
        try:
            url = f"{self.api_url}/latest"
            params = {"from": base_currency}

            response = self.client.get(url, params=params)
            response.raise_for_status()

            data: dict[str, Any] = response.json()
            rates = data.get("rates", {})

            # Include the base currency with rate 1.0
            rates[base_currency] = 1.0

            logger.debug(
                "Fetched exchange rates",
                base_currency=base_currency,
                rate_count=len(rates),
            )

            return rates

        except httpx.HTTPError as e:
            logger.error("Failed to fetch exchange rates", error=str(e))
            raise CurrencyConversionError(f"Failed to fetch exchange rates: {e}") from e

    def get_rate(
        self,
        from_currency: str,
        to_currency: str = DEFAULT_TARGET_CURRENCY,
        use_fallback: bool = True,
    ) -> float:
        """Get exchange rate between two currencies.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code (default EUR)
            use_fallback: Whether to use fallback rates if API fails

        Returns:
            Exchange rate (multiply amount in from_currency to get to_currency)

        Raises:
            CurrencyConversionError: If rate cannot be determined
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return 1.0

        # Check cache first
        cached_rates = self.cache.get(from_currency)
        if cached_rates and to_currency in cached_rates:
            return cached_rates[to_currency]

        try:
            rates = self._fetch_rates(from_currency)
            self.cache.set(from_currency, rates)

            if to_currency not in rates:
                raise CurrencyConversionError(
                    f"No rate available for {from_currency} -> {to_currency}"
                )

            return rates[to_currency]

        except CurrencyConversionError:
            if not use_fallback:
                raise

            return self._get_fallback_rate(from_currency, to_currency)

    def _get_fallback_rate(self, from_currency: str, to_currency: str) -> float:
        """Get fallback exchange rate.

        Args:
            from_currency: Source currency
            to_currency: Target currency

        Returns:
            Fallback exchange rate

        Raises:
            CurrencyConversionError: If no fallback available
        """
        # Fallback rates are EUR-based
        if from_currency not in FALLBACK_EXCHANGE_RATES:
            raise CurrencyConversionError(
                f"No fallback rate available for {from_currency}"
            )

        if to_currency not in FALLBACK_EXCHANGE_RATES:
            raise CurrencyConversionError(
                f"No fallback rate available for {to_currency}"
            )

        # Convert via EUR
        from_to_eur = 1.0 / FALLBACK_EXCHANGE_RATES[from_currency]
        eur_to_target = FALLBACK_EXCHANGE_RATES[to_currency]

        rate = from_to_eur * eur_to_target

        logger.warning(
            "Using fallback exchange rate",
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
        )

        return rate

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str = DEFAULT_TARGET_CURRENCY,
        use_fallback: bool = True,
    ) -> tuple[float, float]:
        """Convert an amount between currencies.

        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency (default EUR)
            use_fallback: Whether to use fallback rates if API fails

        Returns:
            Tuple of (converted_amount, exchange_rate)

        Raises:
            CurrencyConversionError: If conversion fails
        """
        rate = self.get_rate(from_currency, to_currency, use_fallback)
        converted = amount * rate

        logger.debug(
            "Currency conversion",
            amount=amount,
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            converted=converted,
        )

        return converted, rate
