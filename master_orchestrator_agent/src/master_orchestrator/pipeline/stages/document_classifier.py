"""Document Classifier Stage - Classifies documents by type using hybrid strategy."""

import structlog

from master_orchestrator.config.constants import (
    DocumentCategory,
    ClassificationStrategy,
    FILENAME_PATTERNS,
)
from master_orchestrator.models.input import DocumentInfo, DocumentBatch, ClassificationResult
from master_orchestrator.pipeline.base import MasterPipelineContext, MasterPipelineStage
from master_orchestrator.services.llm_service import LLMService
from master_orchestrator.utils.exceptions import ClassificationError, MissingDocumentCategoryError

logger = structlog.get_logger(__name__)


class DocumentClassifierStage(MasterPipelineStage):
    """Stage 2: Classify documents by type using filename patterns or LLM."""

    def __init__(self, llm_service: LLMService | None = None):
        self._llm_service = llm_service

    @property
    def name(self) -> str:
        return "DocumentClassifier"

    def process(self, context: MasterPipelineContext) -> MasterPipelineContext:
        """Classify all scanned documents."""
        logger.info(
            "classifying_documents",
            count=len(context.scanned_documents),
            strategy=str(context.settings.classification_strategy),
        )

        strategy = context.settings.classification_strategy
        batch = DocumentBatch()

        for doc in context.scanned_documents:
            try:
                result = self._classify_document(doc, strategy, context)
                doc.category = result.category
                doc.classification_confidence = result.confidence
                doc.classification_method = result.method

                # Add to appropriate batch
                self._add_to_batch(doc, batch)

                logger.debug(
                    "document_classified",
                    file=doc.file_name,
                    category=result.category.value,
                    confidence=result.confidence,
                    method=result.method,
                )

            except Exception as e:
                context.add_error(f"Failed to classify {doc.file_name}: {str(e)}")
                doc.category = DocumentCategory.UNKNOWN
                batch.unknown_documents.append(doc)

        context.document_batch = batch

        # Log classification summary
        logger.info(
            "classification_complete",
            passport=len(batch.passport_documents),
            financial=len(batch.financial_documents),
            education=len(batch.education_documents),
            unknown=len(batch.unknown_documents),
        )

        # Support flexible document sets: only error if NOTHING useful was found
        # Total scanned documents are already checked in Stage 1.
        has_passport = len(batch.passport_documents) > 0
        has_financial = len(batch.financial_documents) > 0
        has_education = len(batch.education_documents) > 0

        if not (has_passport or has_financial or has_education):
            # No relevant documents recognized at all
            raise ClassificationError(
                "No documents were recognized as a Passport, Financial document, or Education certificate. "
                "Please ensure files are clearly legible, use supported formats, and follow naming conventions."
            )

        # Log warnings for missing categories instead of failing
        missing = batch.missing_categories
        if missing:
            missing_names = [cat.value if hasattr(cat, "value") else str(cat) for cat in missing]
            context.add_warning(f"Missing recommended document categories: {', '.join(missing_names)}")
            logger.warning("missing_document_categories", missing=missing_names)

        return context

    def _classify_document(
        self,
        doc: DocumentInfo,
        strategy: ClassificationStrategy,
        context: MasterPipelineContext,
    ) -> ClassificationResult:
        """Classify a single document based on strategy."""
        # Try filename-based classification first (unless LLM-only)
        if strategy != ClassificationStrategy.LLM_ONLY:
            filename_result = self._classify_by_filename(doc)
            if filename_result.category != DocumentCategory.UNKNOWN:
                return filename_result

        # Use LLM fallback if needed (unless filename-only)
        if strategy != ClassificationStrategy.FILENAME_ONLY:
            if self._llm_service is None:
                self._llm_service = LLMService(context.settings)

            llm_result = self._classify_by_llm(doc, context)
            if llm_result:
                return llm_result

        # Return unknown if classification failed
        return ClassificationResult(
            category=DocumentCategory.UNKNOWN,
            confidence=0.0,
            method="none",
            reasoning="Could not classify document",
        )

    def _classify_by_filename(self, doc: DocumentInfo) -> ClassificationResult:
        """Classify document based on filename patterns."""
        filename_lower = doc.file_name.lower()

        for category, patterns in FILENAME_PATTERNS.items():
            for pattern in patterns:
                if pattern in filename_lower:
                    return ClassificationResult(
                        category=category,
                        confidence=0.9,  # High confidence for filename match
                        method="filename",
                        reasoning=f"Filename contains pattern: {pattern}",
                    )

        return ClassificationResult(
            category=DocumentCategory.UNKNOWN,
            confidence=0.0,
            method="filename",
            reasoning="No filename pattern matched",
        )

    def _classify_by_llm(
        self,
        doc: DocumentInfo,
        context: MasterPipelineContext,
    ) -> ClassificationResult | None:
        """Classify document using LLM vision."""
        if self._llm_service is None:
            return None

        try:
            result = self._llm_service.classify_document(doc.file_path)
            return result
        except Exception as e:
            context.add_warning(f"LLM classification failed for {doc.file_name}: {str(e)}")
            return None

    def _add_to_batch(self, doc: DocumentInfo, batch: DocumentBatch) -> None:
        """Add document to appropriate batch category."""
        match doc.category:
            case DocumentCategory.PASSPORT:
                batch.passport_documents.append(doc)
            case DocumentCategory.FINANCIAL:
                batch.financial_documents.append(doc)
            case DocumentCategory.EDUCATION:
                batch.education_documents.append(doc)
            case _:
                batch.unknown_documents.append(doc)
