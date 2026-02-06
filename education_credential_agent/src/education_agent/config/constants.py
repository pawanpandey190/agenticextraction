"""Constants and enums for the education credential agent."""

from enum import Enum


class AcademicLevel(str, Enum):
    """Academic qualification levels with ranking."""

    SECONDARY = "SECONDARY"      # Rank 1 - High school / Secondary education
    DIPLOMA = "DIPLOMA"          # Rank 2 - Diploma / Certificate programs
    BACHELOR = "BACHELOR"        # Rank 3 - Bachelor's degree
    MASTER = "MASTER"            # Rank 4 - Master's degree
    DOCTORATE = "DOCTORATE"      # Rank 5 - PhD / Doctorate
    TRANSCRIPT = "TRANSCRIPT"    # Rank 0 - Academic transcript (no degree)
    OTHER = "OTHER"              # Rank 0 - Unclassified

    @property
    def rank(self) -> int:
        """Get the rank of the academic level for comparison."""
        rank_map = {
            AcademicLevel.SECONDARY: 1,
            AcademicLevel.DIPLOMA: 2,
            AcademicLevel.BACHELOR: 3,
            AcademicLevel.MASTER: 4,
            AcademicLevel.DOCTORATE: 5,
            AcademicLevel.TRANSCRIPT: 0,
            AcademicLevel.OTHER: 0,
        }
        return rank_map.get(self, 0)


class DocumentType(str, Enum):
    """Types of education documents supported."""

    DEGREE_CERTIFICATE = "DEGREE_CERTIFICATE"
    TRANSCRIPT = "TRANSCRIPT"
    MARK_SHEET = "MARK_SHEET"
    DIPLOMA = "DIPLOMA"
    SEMESTER_MARK_SHEET = "SEMESTER_MARK_SHEET"
    CONSOLIDATED_MARK_SHEET = "CONSOLIDATED_MARK_SHEET"
    PROVISIONAL_CERTIFICATE = "PROVISIONAL_CERTIFICATE"
    UNKNOWN = "UNKNOWN"


class GradingSystem(str, Enum):
    """Grading systems used worldwide."""

    PERCENTAGE = "PERCENTAGE"           # 0-100%
    GPA_4 = "GPA_4"                     # 0.0-4.0 scale
    GPA_10 = "GPA_10"                   # 0.0-10.0 scale (India)
    LETTER_GRADE = "LETTER_GRADE"       # A, B, C, D, F
    FRENCH_20 = "FRENCH_20"             # 0-20 scale (France)
    UK_HONORS = "UK_HONORS"             # First, 2:1, 2:2, Third
    GERMAN_5 = "GERMAN_5"               # 1.0-5.0 (1.0 is best)
    OTHER = "OTHER"


class SemesterValidationStatus(str, Enum):
    """Status of semester validation for Bachelor's degrees."""

    COMPLETE = "COMPLETE"               # All semesters present
    INCOMPLETE = "INCOMPLETE"           # Missing semesters
    NOT_APPLICABLE = "NOT_APPLICABLE"   # Not a Bachelor's degree
    COMPLETE_VIA_CONSOLIDATED = "COMPLETE_VIA_CONSOLIDATED"  # Complete via consolidated mark sheet


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

# Bachelor's degree programs and their expected semesters
BACHELOR_SEMESTER_MAP = {
    # 4-year programs (8 semesters)
    "B.TECH": 8,
    "BACHELOR OF TECHNOLOGY": 8,
    "B.E.": 8,
    "BACHELOR OF ENGINEERING": 8,
    "B.ARCH": 10,
    "BACHELOR OF ARCHITECTURE": 10,
    # 3-year programs (6 semesters)
    "B.SC": 6,
    "BACHELOR OF SCIENCE": 6,
    "B.A.": 6,
    "BACHELOR OF ARTS": 6,
    "B.COM": 6,
    "BACHELOR OF COMMERCE": 6,
    "BBA": 6,
    "BACHELOR OF BUSINESS ADMINISTRATION": 6,
    "B.CA": 6,
    "BACHELOR OF COMPUTER APPLICATIONS": 6,
    "BCA": 6,
    # Default for unknown bachelor programs
    "DEFAULT": 8,
}

# ISO 3166-1 alpha-2 country codes commonly encountered
COUNTRY_CODES = {
    "IN": "India",
    "US": "United States",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "CN": "China",
    "JP": "Japan",
    "AU": "Australia",
    "CA": "Canada",
    "BR": "Brazil",
    "RU": "Russia",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BE": "Belgium",
    "CH": "Switzerland",
    "PK": "Pakistan",
    "BD": "Bangladesh",
    "LK": "Sri Lanka",
    "NP": "Nepal",
    "NG": "Nigeria",
    "KE": "Kenya",
    "ZA": "South Africa",
    "AE": "United Arab Emirates",
    "SA": "Saudi Arabia",
    "SG": "Singapore",
    "MY": "Malaysia",
    "PH": "Philippines",
    "VN": "Vietnam",
    "TH": "Thailand",
    "ID": "Indonesia",
    "MX": "Mexico",
    "AR": "Argentina",
    "CO": "Colombia",
    "CL": "Chile",
    "EG": "Egypt",
    "TR": "Turkey",
    "PL": "Poland",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "FI": "Finland",
    "IE": "Ireland",
    "PT": "Portugal",
    "AT": "Austria",
    "NZ": "New Zealand",
}
