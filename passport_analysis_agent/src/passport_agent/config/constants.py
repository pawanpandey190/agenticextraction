"""Constants and enums for the passport analysis agent."""

from enum import Enum


class FileType(str, Enum):
    """Supported file types."""

    PDF = "pdf"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


class Sex(str, Enum):
    """Sex/Gender values in passports."""

    MALE = "M"
    FEMALE = "F"
    UNSPECIFIED = "X"
    MRZ_PLACEHOLDER = "<"


class ConfidenceLevel(str, Enum):
    """Confidence level for analysis results."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MatchType(str, Enum):
    """Match type for field comparison."""

    MATCH = "match"
    MISMATCH = "mismatch"


# Magic bytes for file type detection
FILE_SIGNATURES: dict[bytes, FileType] = {
    b"%PDF": FileType.PDF,
    b"\x89PNG": FileType.PNG,
    b"\xff\xd8\xff": FileType.JPEG,
}

# Supported MIME types
SUPPORTED_MIME_TYPES: dict[str, FileType] = {
    "application/pdf": FileType.PDF,
    "image/png": FileType.PNG,
    "image/jpeg": FileType.JPEG,
}

# MRZ Check Digit Weights (ICAO 9303)
MRZ_WEIGHTS: list[int] = [7, 3, 1]

# MRZ Character Values (ICAO 9303)
MRZ_VALUES: dict[str, int] = {
    "<": 0,
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "A": 10,
    "B": 11,
    "C": 12,
    "D": 13,
    "E": 14,
    "F": 15,
    "G": 16,
    "H": 17,
    "I": 18,
    "J": 19,
    "K": 20,
    "L": 21,
    "M": 22,
    "N": 23,
    "O": 24,
    "P": 25,
    "Q": 26,
    "R": 27,
    "S": 28,
    "T": 29,
    "U": 30,
    "V": 31,
    "W": 32,
    "X": 33,
    "Y": 34,
    "Z": 35,
}

# ICAO Country Codes (3-letter)
# This is a subset of commonly used codes
ICAO_COUNTRY_CODES: set[str] = {
    # Special codes
    "UTO",  # ICAO test passport
    "XXX",  # Unspecified
    "XOM",  # International Organization for Migration
    "UNO",  # United Nations Organization
    # Common countries
    "USA",
    "GBR",
    "DEU",
    "FRA",
    "ITA",
    "ESP",
    "NLD",
    "BEL",
    "AUT",
    "CHE",
    "PRT",
    "GRC",
    "POL",
    "CZE",
    "HUN",
    "ROU",
    "BGR",
    "HRV",
    "SVN",
    "SVK",
    "SRB",
    "UKR",
    "RUS",
    "JPN",
    "CHN",
    "KOR",
    "TWN",
    "HKG",
    "SGP",
    "MYS",
    "THA",
    "VNM",
    "PHL",
    "IDN",
    "IND",
    "PAK",
    "BGD",
    "LKA",
    "NPL",
    "AUS",
    "NZL",
    "CAN",
    "MEX",
    "BRA",
    "ARG",
    "CHL",
    "COL",
    "PER",
    "VEN",
    "ECU",
    "ZAF",
    "EGY",
    "MAR",
    "NGA",
    "KEN",
    "GHA",
    "TZA",
    "ETH",
    "SAU",
    "ARE",
    "ISR",
    "TUR",
    "IRN",
    "IRQ",
    "SYR",
    "JOR",
    "LBN",
    "KWT",
    "QAT",
    "BHR",
    "OMN",
    # European Union country codes
    "DNK",
    "SWE",
    "NOR",
    "FIN",
    "IRL",
    "LUX",
    "MLT",
    "CYP",
    "EST",
    "LVA",
    "LTU",
    # D for Germany (alternative)
    "D<<",
}

# TD3 MRZ Line positions
TD3_LINE_LENGTH = 44
TD3_TOTAL_LENGTH = 88

# Line 2 field positions (0-indexed)
TD3_LINE2_PASSPORT_NUMBER_START = 0
TD3_LINE2_PASSPORT_NUMBER_END = 9
TD3_LINE2_PASSPORT_CHECK = 9
TD3_LINE2_NATIONALITY_START = 10
TD3_LINE2_NATIONALITY_END = 13
TD3_LINE2_DOB_START = 13
TD3_LINE2_DOB_END = 19
TD3_LINE2_DOB_CHECK = 19
TD3_LINE2_SEX = 20
TD3_LINE2_EXPIRY_START = 21
TD3_LINE2_EXPIRY_END = 27
TD3_LINE2_EXPIRY_CHECK = 27
TD3_LINE2_PERSONAL_NUMBER_START = 28
TD3_LINE2_PERSONAL_NUMBER_END = 42
TD3_LINE2_PERSONAL_CHECK = 42
TD3_LINE2_COMPOSITE_CHECK = 43

# Fields to cross-validate
CROSS_VALIDATION_FIELDS = [
    "first_name",
    "last_name",
    "date_of_birth",
    "passport_number",
    "sex",
    "issuing_country",
    "expiry_date",
]

# Fields that use fuzzy matching
FUZZY_MATCH_FIELDS = {"first_name", "last_name"}

# Fields that require exact matching
EXACT_MATCH_FIELDS = {
    "date_of_birth",
    "passport_number",
    "sex",
    "issuing_country",
    "expiry_date",
}

# Scoring weights
SCORE_WEIGHT_CHECKSUMS = 40
SCORE_WEIGHT_FIELD_MATCHES = 40
SCORE_WEIGHT_OCR_CONFIDENCE = 20

# Confidence thresholds
CONFIDENCE_HIGH_THRESHOLD = 85
CONFIDENCE_MEDIUM_THRESHOLD = 60
