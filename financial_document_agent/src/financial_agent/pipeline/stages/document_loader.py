"""Document loading stage."""

from pathlib import Path

from PIL import Image

from ...config.constants import FILE_SIGNATURES, FileType
from ...config.settings import Settings
from ...models.document import DocumentInput, DocumentPage
from ...utils.exceptions import DocumentLoadError
from ...utils.image_utils import encode_image_base64, image_to_bytes, resize_image_if_needed
from ...utils.pdf_utils import pdf_to_images
from ..base import PipelineContext, PipelineStage


class DocumentLoaderStage(PipelineStage):
    """Stage for loading and validating documents."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    @property
    def name(self) -> str:
        return "document_loader"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Load and validate the document.

        Args:
            context: Pipeline context

        Returns:
            Updated context with loaded document

        Raises:
            DocumentLoadError: If document cannot be loaded
        """
        file_path = Path(context.file_path)

        # Validate file exists
        if not file_path.exists():
            raise DocumentLoadError(f"File not found: {file_path}")

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.settings.max_file_size_bytes:
            raise DocumentLoadError(
                f"File too large: {file_size} bytes (max {self.settings.max_file_size_bytes})"
            )

        # Detect file type
        file_type = self._detect_file_type(file_path)

        # Load pages
        pages = self._load_pages(file_path, file_type)

        # Create document input
        document = DocumentInput(
            file_path=file_path,
            file_type=file_type,
            file_size_bytes=file_size,
            pages=pages,
            original_filename=file_path.name,
        )

        context.document = document
        context.metadata.pages_processed = len(pages)

        # Store first page for classification
        if pages:
            first_page = pages[0]
            image = Image.open(Path(file_path).parent / "temp_first_page.png") if False else None

            # Re-encode first page for potential image-based classification
            from ...utils.image_utils import bytes_to_image

            img = bytes_to_image(first_page.image_data)
            img = resize_image_if_needed(img)
            base64_data, mime_type = encode_image_base64(img)
            context.first_page_base64 = base64_data
            context.first_page_mime_type = mime_type

        self.logger.info(
            "Document loaded",
            file_type=file_type.value,
            page_count=len(pages),
            file_size=file_size,
        )

        context.set_stage_result(self.name, {
            "file_type": file_type.value,
            "page_count": len(pages),
            "file_size": file_size,
        })

        return context

    def _detect_file_type(self, file_path: Path) -> FileType:
        """Detect file type from magic bytes.

        Args:
            file_path: Path to the file

        Returns:
            Detected file type

        Raises:
            DocumentLoadError: If file type is not supported
        """
        with open(file_path, "rb") as f:
            header = f.read(8)

        for signature, file_type in FILE_SIGNATURES.items():
            if header.startswith(signature):
                return file_type

        # Fallback to extension
        ext = file_path.suffix.lower().lstrip(".")
        try:
            return FileType(ext)
        except ValueError:
            raise DocumentLoadError(
                f"Unsupported file type: {file_path.suffix}",
                details={"supported": [ft.value for ft in FileType]},
            )

    def _load_pages(self, file_path: Path, file_type: FileType) -> list[DocumentPage]:
        """Load document pages.

        Args:
            file_path: Path to the file
            file_type: Detected file type

        Returns:
            List of document pages

        Raises:
            DocumentLoadError: If pages cannot be loaded
        """
        if file_type == FileType.PDF:
            return self._load_pdf_pages(file_path)
        else:
            return self._load_image_page(file_path, file_type)

    def _load_pdf_pages(self, file_path: Path) -> list[DocumentPage]:
        """Load pages from a PDF file.

        Args:
            file_path: Path to the PDF

        Returns:
            List of document pages
        """
        images = pdf_to_images(file_path, max_pages=self.settings.max_pdf_pages)
        pages = []

        for i, image in enumerate(images, 1):
            # Resize if needed
            image = resize_image_if_needed(image)

            # Convert to bytes
            image_bytes = image_to_bytes(image, format="PNG")

            page = DocumentPage(
                page_number=i,
                image_data=image_bytes,
                width=image.width,
                height=image.height,
                mime_type="image/png",
            )
            pages.append(page)

        return pages

    def _load_image_page(self, file_path: Path, file_type: FileType) -> list[DocumentPage]:
        """Load a single image file as a page.

        Args:
            file_path: Path to the image
            file_type: Image file type

        Returns:
            List with single document page
        """
        try:
            image = Image.open(file_path)

            # Convert to RGB if necessary
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")

            # Resize if needed
            image = resize_image_if_needed(image)

            # Determine format and mime type
            if file_type in (FileType.JPEG, FileType.JPG):
                format = "JPEG"
                mime_type = "image/jpeg"
            else:
                format = "PNG"
                mime_type = "image/png"

            image_bytes = image_to_bytes(image, format=format)

            page = DocumentPage(
                page_number=1,
                image_data=image_bytes,
                width=image.width,
                height=image.height,
                mime_type=mime_type,
            )

            return [page]

        except Exception as e:
            raise DocumentLoadError(f"Failed to load image: {e}") from e
