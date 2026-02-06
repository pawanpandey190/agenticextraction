"""Document Scanner Stage - Scans input folder for supported documents."""

import structlog

from master_orchestrator.config.constants import SUPPORTED_FILE_EXTENSIONS
from master_orchestrator.models.input import DocumentInfo
from master_orchestrator.pipeline.base import MasterPipelineContext, MasterPipelineStage
from master_orchestrator.utils.exceptions import DocumentScanError

logger = structlog.get_logger(__name__)


class DocumentScannerStage(MasterPipelineStage):
    """Stage 1: Scan input folder for supported documents."""

    @property
    def name(self) -> str:
        return "DocumentScanner"

    def process(self, context: MasterPipelineContext) -> MasterPipelineContext:
        """Scan folder for documents and validate file sizes."""
        logger.info("scanning_folder", folder=str(context.input_folder))

        if not context.input_folder.exists():
            raise DocumentScanError(
                f"Input folder does not exist: {context.input_folder}",
                {"folder": str(context.input_folder)},
            )

        if not context.input_folder.is_dir():
            raise DocumentScanError(
                f"Input path is not a directory: {context.input_folder}",
                {"folder": str(context.input_folder)},
            )

        documents: list[DocumentInfo] = []
        max_size = context.settings.max_file_size_bytes

        # Scan for supported files
        for file_path in context.input_folder.iterdir():
            if not file_path.is_file():
                continue

            extension = file_path.suffix.lower()
            if extension not in SUPPORTED_FILE_EXTENSIONS:
                logger.debug("skipping_unsupported_file", file=file_path.name)
                continue

            # Check file size
            file_size = file_path.stat().st_size
            if file_size > max_size:
                context.add_warning(
                    f"File {file_path.name} exceeds size limit "
                    f"({file_size} > {max_size} bytes), skipping"
                )
                continue

            if file_size == 0:
                context.add_warning(f"File {file_path.name} is empty, skipping")
                continue

            doc_info = DocumentInfo.from_path(file_path)
            documents.append(doc_info)
            logger.debug(
                "found_document",
                file=file_path.name,
                size=file_size,
                extension=extension,
            )

        if not documents:
            raise DocumentScanError(
                f"No supported documents found in folder: {context.input_folder}",
                {
                    "folder": str(context.input_folder),
                    "supported_extensions": list(SUPPORTED_FILE_EXTENSIONS),
                },
            )

        context.scanned_documents = documents
        logger.info(
            "scan_complete",
            total_documents=len(documents),
            folder=str(context.input_folder),
        )

        return context
