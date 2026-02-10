"""Constants and enums for the financial agent."""

from enum import Enum


class DocumentType(str, Enum):
    """Types of financial documents supported."""

    BANK_STATEMENT = "BANK_STATEMENT"
    BANK_LETTER = "BANK_LETTER"
    CERTIFICATE = "CERTIFICATE"
    UNKNOWN = "UNKNOWN"


class CurrencyConfidence(str, Enum):
    """Confidence level for currency detection."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ConsistencyStatus(str, Enum):
    """Account consistency status."""

    CONSISTENT = "CONSISTENT"
    INCONSISTENT = "INCONSISTENT"
    PARTIAL = "PARTIAL"


class WorthinessDecision(str, Enum):
    """Financial worthiness decision."""

    WORTHY = "WORTHY"
    NOT_WORTHY = "NOT_WORTHY"
    INCONCLUSIVE = "INCONCLUSIVE"


class OCRStrategy(str, Enum):
    """OCR strategy options."""

    ANTHROPIC_VISION = "anthropic_vision"
    TESSERACT = "tesseract"
    AUTO = "auto"


class FileType(str, Enum):
    """Supported file types."""

    PDF = "pdf"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


# Magic bytes for file type detection
FILE_SIGNATURES = {
    b"%PDF": FileType.PDF,
    b"\x89PNG": FileType.PNG,
    b"\xff\xd8\xff": FileType.JPEG,
}

# Supported MIME types
SUPPORTED_MIME_TYPES = {
    "application/pdf": FileType.PDF,
    "image/png": FileType.PNG,
    "image/jpeg": FileType.JPEG,
}

# Default currency for conversion
DEFAULT_TARGET_CURRENCY = "EUR"

# Common currency symbols mapping
CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "CHF": "CHF",
    "Fr.": "CHF",
    "kr": "SEK",  # Could also be NOK, DKK
    "₹": "INR",
    "R$": "BRL",
    "A$": "AUD",
    "C$": "CAD",
    "¥": "CNY",  # Could also be JPY
}

# Fallback exchange rates (EUR base) - used when API is unavailable
# Rate = how many units of currency per 1 EUR
FALLBACK_EXCHANGE_RATES = {
    "USD": 1.08,
    "GBP": 0.86,
    "CHF": 0.95,
    "JPY": 162.0,
    "SEK": 11.5,
    "NOK": 11.8,
    "DKK": 7.46,
    "INR": 90.0,
    "BRL": 5.4,
    "AUD": 1.65,
    "CAD": 1.48,
    "CNY": 7.8,
    "KWD": 0.33,  # Kuwaiti Dinar (1 KWD ≈ 3.0 EUR)
    "AED": 3.97,  # UAE Dirham
    "SAR": 4.05,  # Saudi Riyal
    "QAR": 3.93,  # Qatari Riyal
    "BHD": 0.41,  # Bahraini Dinar
    "OMR": 0.42,  # Omani Rial
    "BDT": 130.0,  # Bangladeshi Taka
    "PKR": 300.0,  # Pakistani Rupee
    "LKR": 350.0,  # Sri Lankan Rupee
    "NPR": 145.0,  # Nepalese Rupee
    "IRR": 45000.0,  # Iranian Rial
    "IQD": 1420.0,  # Iraqi Dinar
    "TRY": 38.0,  # Turkish Lira
    "EGP": 53.0,  # Egyptian Pound
    "ETB": 130.0,  # Ethiopian Birr
    "KES": 140.0,  # Kenyan Shilling
    "NGN": 1700.0,  # Nigerian Naira
    "ZAR": 20.0,  # South African Rand
    "GHS": 17.0,  # Ghanaian Cedi
    "EUR": 1.0,
}
