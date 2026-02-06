"""Document classification stage."""

from ...config.constants import DocumentType
from ...config.settings import Settings
from ...prompts.classification import CLASSIFICATION_PROMPT, CLASSIFICATION_WITH_IMAGE_PROMPT
from ...prompts.system import SYSTEM_PROMPT
from ...services.llm_service import LLMService
from ...utils.exceptions import ClassificationError
from ..base import PipelineContext, PipelineStage


class ClassifierStage(PipelineStage):
    """Stage for classifying document type."""

    def __init__(self, settings: Settings, llm_service: LLMService | None = None) -> None:
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)

    @property
    def name(self) -> str:
        return "classifier"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Classify the document type.

        Args:
            context: Pipeline context

        Returns:
            Updated context with classification

        Raises:
            ClassificationError: If classification fails
        """
        if not context.extracted_text:
            raise ClassificationError("No extracted text for classification")

        try:
            # Use image-based classification if available
            if context.first_page_base64 and context.first_page_mime_type:
                result = self.llm_service.classify_document(
                    text=context.extracted_text,
                    image_base64=context.first_page_base64,
                    mime_type=context.first_page_mime_type,
                    system_prompt=SYSTEM_PROMPT,
                    classification_prompt=CLASSIFICATION_WITH_IMAGE_PROMPT,
                )
            else:
                result = self.llm_service.classify_document(
                    text=context.extracted_text,
                    system_prompt=SYSTEM_PROMPT,
                    classification_prompt=CLASSIFICATION_PROMPT,
                )

            # Parse classification result
            document_type = self._parse_document_type(result.get("document_type", "UNKNOWN"))
            confidence = float(result.get("confidence", 0.5))
            reasoning = result.get("reasoning", "")
            key_indicators = result.get("key_indicators", [])

            self.logger.info(
                "Document classified",
                document_type=document_type.value,
                confidence=confidence,
                reasoning=reasoning,
            )

            context.set_stage_result(self.name, {
                "document_type": document_type.value,
                "confidence": confidence,
                "reasoning": reasoning,
                "key_indicators": key_indicators,
            })

            # Store in context for later stages
            if context.financial_data is None:
                from ...models.financial_data import FinancialData
                context.financial_data = FinancialData(document_type=document_type)
            else:
                context.financial_data.document_type = document_type

            return context

        except Exception as e:
            self.logger.error("Classification failed", error=str(e))
            raise ClassificationError(f"Failed to classify document: {e}") from e

    def _parse_document_type(self, type_str: str) -> DocumentType:
        """Parse document type from string.

        Args:
            type_str: Document type string

        Returns:
            DocumentType enum value
        """
        type_str = type_str.upper().strip()

        try:
            return DocumentType(type_str)
        except ValueError:
            self.logger.warning(f"Unknown document type: {type_str}, defaulting to UNKNOWN")
            return DocumentType.UNKNOWN
