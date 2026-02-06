"""PDF processing utilities using pypdfium2."""

import gc
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

from .exceptions import DocumentLoadError

# Default DPI for rendering PDF pages
DEFAULT_DPI = 200
# Maximum DPI allowed
MAX_DPI = 300
# Default number of worker threads (Set to 1 for stability on macOS ARM64)
DEFAULT_MAX_WORKERS = 1


def _render_page_from_path(
    pdf_path: Path,
    page_index: int,
    scale: float,
) -> tuple[int, Image.Image]:
    """Render a single page from a PDF file.

    Opens its own PDF handle for thread safety.

    Args:
        pdf_path: Path to the PDF file
        page_index: 0-based page index
        scale: Rendering scale factor

    Returns:
        Tuple of (page_index, PIL Image)
    """
    with pdfium.PdfDocument(pdf_path) as pdf:
        page = pdf[page_index]
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
    return (page_index, pil_image)


def _render_page_from_bytes(
    pdf_bytes: bytes,
    page_index: int,
    scale: float,
) -> tuple[int, Image.Image]:
    """Render a single page from PDF bytes.

    Opens its own PDF handle for thread safety.

    Args:
        pdf_bytes: PDF file content as bytes
        page_index: 0-based page index
        scale: Rendering scale factor

    Returns:
        Tuple of (page_index, PIL Image)
    """
    with pdfium.PdfDocument(pdf_bytes) as pdf:
        page = pdf[page_index]
        bitmap = page.render(scale=scale)
        pil_image = bitmap.to_pil()
    return (page_index, pil_image)


def pdf_to_images(
    pdf_path: Path | str,
    max_pages: int | None = None,
    dpi: int = DEFAULT_DPI,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> list[Image.Image]:
    """Convert a PDF file to a list of PIL Images.

    Uses parallel rendering for multi-page PDFs.

    Args:
        pdf_path: Path to the PDF file
        max_pages: Maximum number of pages to convert (None for all)
        dpi: Resolution for rendering (default 200)
        max_workers: Maximum concurrent rendering threads (default 4)

    Returns:
        List of PIL Image objects, one per page

    Raises:
        DocumentLoadError: If PDF cannot be loaded or converted
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise DocumentLoadError(f"PDF file not found: {pdf_path}")

    if dpi > MAX_DPI:
        dpi = MAX_DPI

    try:
        # Read file into memory first to ensure handle is closed and data is fully available
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        with pdfium.PdfDocument(pdf_bytes) as pdf:
            page_count = len(pdf)

            if max_pages is not None:
                page_count = min(page_count, max_pages)

            scale = dpi / 72  # PDF uses 72 DPI internally

            # For single page, no parallelization needed
            if page_count == 1:
                page = pdf[0]
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil()
                return [image]

            # Reduce workers for large files to prevent memory corruption
            file_size_mb = len(pdf_bytes) / (1024 * 1024)
            if file_size_mb > 5:  # Large file (>5MB)
                max_workers = 1  # Sequential processing for large files
            elif file_size_mb > 2:  # Medium file (>2MB)
                max_workers = min(max_workers, 2)  # Use only 2 workers
        
        # Parallel rendering for multiple pages
        images: dict[int, Image.Image] = {}

        if max_workers <= 1:
            # Simple sequential processing
            for i in range(page_count):
                _, img = _render_page_from_bytes(pdf_bytes, i, scale)
                images[i] = img
                gc.collect()
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(_render_page_from_bytes, pdf_bytes, i, scale): i
                    for i in range(page_count)
                }

                for future in as_completed(futures):
                    page_index, pil_image = future.result()
                    images[page_index] = pil_image
                    # Force garbage collection after each page
                    gc.collect()

        # Return images in page order
        result = [images[i] for i in range(page_count)]
        
        # Final cleanup
        gc.collect()
        
        return result

    except Exception as e:
        # Get more diagnostic info
        file_exists = pdf_path.exists()
        file_size = pdf_path.stat().st_size if file_exists else -1
        raise DocumentLoadError(
            f"Failed to convert PDF to images: {e}",
            details={
                "pdf_path": str(pdf_path),
                "file_exists": file_exists,
                "file_size": file_size,
                "error_type": type(e).__name__
            },
        ) from e


def pdf_bytes_to_images(
    pdf_bytes: bytes,
    max_pages: int | None = None,
    dpi: int = DEFAULT_DPI,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> list[Image.Image]:
    """Convert PDF bytes to a list of PIL Images.

    Uses parallel rendering for multi-page PDFs.

    Args:
        pdf_bytes: PDF file content as bytes
        max_pages: Maximum number of pages to convert (None for all)
        dpi: Resolution for rendering (default 200)
        max_workers: Maximum concurrent rendering threads (default 4)

    Returns:
        List of PIL Image objects, one per page

    Raises:
        DocumentLoadError: If PDF cannot be loaded or converted
    """
    if dpi > MAX_DPI:
        dpi = MAX_DPI

    try:
        with pdfium.PdfDocument(pdf_bytes) as pdf:
            page_count = len(pdf)

            if max_pages is not None:
                page_count = min(page_count, max_pages)

            scale = dpi / 72

            # For single page, no parallelization needed
            if page_count == 1:
                page = pdf[0]
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil()
                return [image]

            # Reduce workers for large files
            pdf_size_mb = len(pdf_bytes) / (1024 * 1024)
            if pdf_size_mb > 5:
                max_workers = 1  # Sequential for large files
            elif pdf_size_mb > 2:
                max_workers = min(max_workers, 2)
        
        # Parallel rendering for multiple pages
        images: dict[int, Image.Image] = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(_render_page_from_bytes, pdf_bytes, i, scale): i
                for i in range(page_count)
            }

            for future in as_completed(futures):
                page_index, pil_image = future.result()
                images[page_index] = pil_image
                gc.collect()

        # Return images in page order
        result = [images[i] for i in range(page_count)]
        gc.collect()
        
        return result

    except Exception as e:
        raise DocumentLoadError(f"Failed to convert PDF bytes to images: {e}") from e


def get_pdf_page_count(pdf_path: Path | str) -> int:
    """Get the number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages

    Raises:
        DocumentLoadError: If PDF cannot be loaded
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise DocumentLoadError(f"PDF file not found: {pdf_path}")

    try:
        with pdfium.PdfDocument(pdf_path) as pdf:
            return len(pdf)
    except Exception as e:
        raise DocumentLoadError(
            f"Failed to get PDF page count: {e}",
            details={"pdf_path": str(pdf_path)},
        ) from e


def is_valid_pdf(data: bytes) -> bool:
    """Check if bytes represent a valid PDF.

    Args:
        data: File content as bytes

    Returns:
        True if valid PDF, False otherwise
    """
    try:
        with pdfium.PdfDocument(data):
            return True
    except Exception:
        return False
