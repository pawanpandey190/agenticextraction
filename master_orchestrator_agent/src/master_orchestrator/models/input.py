"""Input models for Master Orchestrator Agent."""

from pathlib import Path
from pydantic import BaseModel, Field, computed_field

from master_orchestrator.config.constants import DocumentCategory


class DocumentInfo(BaseModel):
    """Information about a document to be processed."""

    file_path: Path
    file_name: str
    file_extension: str
    file_size_bytes: int
    category: DocumentCategory = DocumentCategory.UNKNOWN
    classification_confidence: float = 0.0
    classification_method: str = ""  # "filename" or "llm"

    @computed_field
    @property
    def is_classified(self) -> bool:
        """Check if document has been classified."""
        return self.category != DocumentCategory.UNKNOWN

    @classmethod
    def from_path(cls, path: Path) -> "DocumentInfo":
        """Create DocumentInfo from a file path."""
        return cls(
            file_path=path,
            file_name=path.name,
            file_extension=path.suffix.lower(),
            file_size_bytes=path.stat().st_size,
        )


class ClassificationResult(BaseModel):
    """Result of document classification."""

    category: DocumentCategory
    confidence: float = Field(ge=0.0, le=1.0)
    method: str  # "filename" or "llm"
    reasoning: str = ""


class DocumentBatch(BaseModel):
    """A batch of documents grouped by category."""

    passport_documents: list[DocumentInfo] = Field(default_factory=list)
    financial_documents: list[DocumentInfo] = Field(default_factory=list)
    education_documents: list[DocumentInfo] = Field(default_factory=list)
    unknown_documents: list[DocumentInfo] = Field(default_factory=list)

    @property
    def total_documents(self) -> int:
        """Total number of documents in the batch."""
        return (
            len(self.passport_documents)
            + len(self.financial_documents)
            + len(self.education_documents)
            + len(self.unknown_documents)
        )

    @property
    def has_all_required_categories(self) -> bool:
        """Check if all required document categories are present."""
        return (
            len(self.passport_documents) > 0
            and len(self.financial_documents) > 0
            and len(self.education_documents) > 0
        )

    @property
    def missing_categories(self) -> list[DocumentCategory]:
        """Get list of missing required categories."""
        missing = []
        if not self.passport_documents:
            missing.append(DocumentCategory.PASSPORT)
        if not self.financial_documents:
            missing.append(DocumentCategory.FINANCIAL)
        if not self.education_documents:
            missing.append(DocumentCategory.EDUCATION)
        return missing
