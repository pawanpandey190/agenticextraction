"""Document loader pipeline stage."""

from pathlib import Path

from PIL import Image

from ...config.constants import FILE_SIGNATURES, FileType
from ...models.document import PassportDocument, PassportPage
from ...utils.exceptions import DocumentLoadError
from ...utils.image_utils import encode_image_base64, resize_image_if_needed
from ...utils.pdf_utils import pdf_to_images
from ..base import PipelineContext, PipelineStage


class DocumentLoaderStage(PipelineStage):
    """Stage 1: Load and validate document, convert to images."""

    @property
    def name(self) -> str:
        return "DocumentLoader"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Load document and convert to images.

        Args:
            context: Pipeline context

        Returns:
            Updated context with document loaded

        Raises:
            DocumentLoadError: If document cannot be loaded
        """
        file_path = Path(context.file_path)

        # Validate file exists
        if not file_path.exists():
            raise DocumentLoadError(f"File not found: {file_path}")

        # Get file size
        file_size = file_path.stat().st_size
        if file_size > context.settings.max_file_size_bytes:
            raise DocumentLoadError(
                f"File too large: {file_size} bytes "
                f"(max: {context.settings.max_file_size_bytes})"
            )

        # Detect file type
        file_type = self._detect_file_type(file_path)
        self.logger.info("Detected file type", file_type=file_type.value)

        # Convert to images
        if file_type == FileType.PDF:
            images = pdf_to_images(
                file_path,
                max_pages=context.settings.max_pdf_pages,
                dpi=context.settings.preprocessing_dpi,
            )
        else:
            # Load image directly
            images = [Image.open(file_path)]

        # Create passport pages
        pages = []
        for i, img in enumerate(images):
            # Resize if needed
            img = resize_image_if_needed(img)

            # Encode to base64
            base64_data, mime_type = encode_image_base64(img, format="PNG")

            page = PassportPage(
                page_number=i + 1,
                image_base64=base64_data,
                mime_type=mime_type,
                width=img.width,
                height=img.height,
            )
            pages.append(page)

        # Create document
        document = PassportDocument(
            file_path=str(file_path.absolute()),
            file_type=file_type,
            file_size_bytes=file_size,
            pages=pages,
        )

        context.document = document
        context.set_stage_result(self.name, {"page_count": len(pages)})

        self.logger.info(
            "Document loaded",
            page_count=len(pages),
            file_type=file_type.value,
            file_size_mb=document.file_size_mb,
        )

        return context

    def _detect_file_type(self, file_path: Path) -> FileType:
        """Detect file type from magic bytes and extension.

        Args:
            file_path: Path to the file

        Returns:
            Detected FileType

        Raises:
            DocumentLoadError: If file type is not supported
        """
        # Read first few bytes for magic number detection
        with open(file_path, "rb") as f:
            header = f.read(8)

        # Check magic bytes
        for signature, file_type in FILE_SIGNATURES.items():
            if header.startswith(signature):
                return file_type

        # Fall back to extension
        ext = file_path.suffix.lower().lstrip(".")
        extension_map = {
            "pdf": FileType.PDF,
            "png": FileType.PNG,
            "jpg": FileType.JPEG,
            "jpeg": FileType.JPEG,
        }

        if ext in extension_map:
            return extension_map[ext]

        raise DocumentLoadError(
            f"Unsupported file type: {file_path.suffix}",
            details={"supported": list(extension_map.keys())},
        )
