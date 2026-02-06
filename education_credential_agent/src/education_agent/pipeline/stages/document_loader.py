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
    """Stage for loading and validating documents from a folder."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    @property
    def name(self) -> str:
        return "document_loader"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Load and validate all documents.

        Args:
            context: Pipeline context

        Returns:
            Updated context with loaded documents

        Raises:
            DocumentLoadError: If no valid documents found
        """
        # Collect all file paths
        all_file_paths: list[str] = []

        # From folder if provided
        if context.folder_path:
            folder = Path(context.folder_path)
            if not folder.exists():
                raise DocumentLoadError(f"Folder not found: {folder}")

            for file_path in folder.iterdir():
                if file_path.is_file() and self._is_supported_file(file_path):
                    all_file_paths.append(str(file_path))

        # Add explicitly provided file paths
        all_file_paths.extend(context.file_paths)

        # Remove duplicates while preserving order
        seen = set()
        unique_paths = []
        for path in all_file_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)

        context.file_paths = unique_paths

        if not context.file_paths:
            raise DocumentLoadError("No supported documents found to process")

        # Load each document
        for file_path in context.file_paths:
            try:
                document = self._load_document(file_path)
                context.documents.append(document)

                # Store first page image for classification
                if document.pages:
                    first_page = document.pages[0]
                    from ...utils.image_utils import bytes_to_image

                    img = bytes_to_image(first_page.image_data)
                    img = resize_image_if_needed(img)
                    base64_data, mime_type = encode_image_base64(img)
                    context.add_first_page_image(file_path, base64_data, mime_type)

                context.metadata.pages_processed += document.page_count

            except Exception as e:
                self.logger.warning(f"Failed to load document: {file_path}", error=str(e))
                context.metadata.add_error(f"Failed to load {file_path}: {e}")

        context.metadata.documents_processed = len(context.documents)

        self.logger.info(
            "Documents loaded",
            total_files=len(context.file_paths),
            loaded_documents=len(context.documents),
            total_pages=context.metadata.pages_processed,
        )

        context.set_stage_result(self.name, {
            "total_files": len(context.file_paths),
            "loaded_documents": len(context.documents),
            "total_pages": context.metadata.pages_processed,
        })

        return context

    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file type is supported.

        Args:
            file_path: Path to the file

        Returns:
            True if supported, False otherwise
        """
        ext = file_path.suffix.lower().lstrip(".")
        return ext in ("pdf", "png", "jpeg", "jpg")

    def _load_document(self, file_path: str) -> DocumentInput:
        """Load a single document.

        Args:
            file_path: Path to the document

        Returns:
            Loaded document

        Raises:
            DocumentLoadError: If document cannot be loaded
        """
        path = Path(file_path)

        # Validate file exists
        if not path.exists():
            raise DocumentLoadError(f"File not found: {path}")

        # Check file size
        file_size = path.stat().st_size
        if file_size > self.settings.max_file_size_bytes:
            raise DocumentLoadError(
                f"File too large: {file_size} bytes (max {self.settings.max_file_size_bytes})"
            )

        # Detect file type
        file_type = self._detect_file_type(path)

        # Load pages
        pages = self._load_pages(path, file_type)

        # Create document input
        return DocumentInput(
            file_path=path,
            file_type=file_type,
            file_size_bytes=file_size,
            pages=pages,
            original_filename=path.name,
        )

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
