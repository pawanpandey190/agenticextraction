"""Document classification stage."""

from ...config.constants import AcademicLevel, DocumentType
from ...config.settings import Settings
from ...models.credential_data import CredentialData
from ...prompts.classification import CLASSIFICATION_PROMPT, CLASSIFICATION_WITH_IMAGE_PROMPT
from ...prompts.system import SYSTEM_PROMPT
from ...services.llm_service import LLMService
from ...utils.exceptions import ClassificationError
from ..base import PipelineContext, PipelineStage


class ClassifierStage(PipelineStage):
    """Stage for classifying document type and academic level."""

    def __init__(self, settings: Settings, llm_service: LLMService | None = None) -> None:
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)

    @property
    def name(self) -> str:
        return "classifier"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Classify all documents.

        Args:
            context: Pipeline context

        Returns:
            Updated context with classifications

        Raises:
            ClassificationError: If classification fails critically
        """
        if not context.extracted_texts:
            raise ClassificationError("No extracted texts for classification")

        for document in context.documents:
            file_path = str(document.file_path)
            extracted_text = context.get_extracted_text(file_path)

            if not extracted_text:
                self.logger.warning(f"No extracted text for {file_path}, skipping classification")
                continue

            try:
                # Get first page image if available
                first_page_image = context.get_first_page_image(file_path)

                if first_page_image:
                    base64_data, mime_type = first_page_image
                    result = self.llm_service.classify_document(
                        text=extracted_text,
                        image_base64=base64_data,
                        mime_type=mime_type,
                        system_prompt=SYSTEM_PROMPT,
                        classification_prompt=CLASSIFICATION_WITH_IMAGE_PROMPT,
                    )
                else:
                    result = self.llm_service.classify_document(
                        text=extracted_text,
                        system_prompt=SYSTEM_PROMPT,
                        classification_prompt=CLASSIFICATION_PROMPT,
                    )

                # Parse classification result
                document_type = self._parse_document_type(result.get("document_type", "UNKNOWN"))
                academic_level = self._parse_academic_level(result.get("academic_level", "OTHER"))
                semester_number = result.get("semester_number")
                is_provisional = result.get("is_provisional", False)
                confidence = float(result.get("confidence", 0.5))

                # Create initial credential data with classification
                credential = CredentialData(
                    source_file=file_path,
                    document_type=document_type,
                    academic_level=academic_level,
                    semester_number=semester_number,
                    is_provisional=is_provisional,
                    confidence_score=confidence,
                    raw_extracted_text=extracted_text,
                )

                context.add_credential(credential)

                self.logger.info(
                    "Document classified",
                    file_path=file_path,
                    document_type=document_type.value,
                    academic_level=academic_level.value,
                    semester_number=semester_number,
                    is_provisional=is_provisional,
                    confidence=confidence,
                )

            except Exception as e:
                self.logger.warning(
                    "Classification failed for document",
                    file_path=file_path,
                    error=str(e),
                )
                context.metadata.add_error(f"Classification failed for {file_path}: {e}")

                # Create credential with unknown classification
                credential = CredentialData(
                    source_file=file_path,
                    document_type=DocumentType.UNKNOWN,
                    academic_level=AcademicLevel.OTHER,
                    confidence_score=0.0,
                    raw_extracted_text=extracted_text,
                )
                context.add_credential(credential)

        self.logger.info(
            "Classification completed",
            total_documents=len(context.documents),
            classified_credentials=len(context.credentials),
        )

        context.set_stage_result(self.name, {
            "total_documents": len(context.documents),
            "classified_credentials": len(context.credentials),
        })

        return context

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

    def _parse_academic_level(self, level_str: str) -> AcademicLevel:
        """Parse academic level from string.

        Args:
            level_str: Academic level string

        Returns:
            AcademicLevel enum value
        """
        level_str = level_str.upper().strip()

        try:
            return AcademicLevel(level_str)
        except ValueError:
            self.logger.warning(f"Unknown academic level: {level_str}, defaulting to OTHER")
            return AcademicLevel.OTHER
