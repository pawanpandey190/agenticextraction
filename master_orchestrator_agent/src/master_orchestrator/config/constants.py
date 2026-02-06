"""Constants and enums for Master Orchestrator Agent."""

from enum import Enum


class DocumentCategory(str, Enum):
    """Categories of documents that can be processed."""

    PASSPORT = "passport"
    FINANCIAL = "financial"
    EDUCATION = "education"
    UNKNOWN = "unknown"


class ClassificationStrategy(str, Enum):
    """Strategies for document classification."""

    HYBRID = "hybrid"  # Filename patterns first, LLM fallback
    LLM_ONLY = "llm_only"  # Always use LLM
    FILENAME_ONLY = "filename_only"  # Only use filename patterns


class OutputFormat(str, Enum):
    """Output format options."""

    JSON = "json"
    EXCEL = "excel"
    BOTH = "both"


class ValidationStatus(str, Enum):
    """Validation status for various checks."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class WorthinessStatus(str, Enum):
    """Financial worthiness status."""

    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


# Supported file extensions
SUPPORTED_FILE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

# Filename patterns for classification (case-insensitive)
FILENAME_PATTERNS: dict[DocumentCategory, list[str]] = {
    DocumentCategory.PASSPORT: [
        "passport",
        "pp_",
        "identity",
        "id_card",
        "travel_document",
    ],
    DocumentCategory.FINANCIAL: [
        "bank",
        "statement",
        "balance",
        "financial",
        "account",
        "certificate_of_balance",
        "bank_letter",
    ],
    DocumentCategory.EDUCATION: [
        "transcript",
        "degree",
        "diploma",
        "certificate",
        "mark_sheet",
        "marksheet",
        "grade",
        "academic",
        "semester",
        "education",
        "qualification",
        "bachelor",
        "master",
        "phd",
    ],
}
