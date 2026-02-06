"""Models module for education credential agent."""

from .credential_data import (
    BachelorValidation,
    CredentialData,
    GradeInfo,
    Institution,
    SemesterRecord,
)
from .document import DocumentInput, DocumentPage, ProcessingMetadata
from .evaluation import (
    AnalysisResult,
    DocumentAnalyzed,
    EvaluationResult,
    GradeConversionResult,
    HighestQualification,
    SemesterValidationResult,
)
from .grade_conversion import (
    CountryGradingSystem,
    GradeConversionTable,
    GradeRange,
    LetterGradeMapping,
)

__all__ = [
    # Document models
    "DocumentInput",
    "DocumentPage",
    "ProcessingMetadata",
    # Credential data models
    "CredentialData",
    "GradeInfo",
    "Institution",
    "SemesterRecord",
    "BachelorValidation",
    # Grade conversion models
    "GradeConversionTable",
    "GradeRange",
    "LetterGradeMapping",
    "CountryGradingSystem",
    # Evaluation models
    "AnalysisResult",
    "DocumentAnalyzed",
    "EvaluationResult",
    "GradeConversionResult",
    "HighestQualification",
    "SemesterValidationResult",
]
