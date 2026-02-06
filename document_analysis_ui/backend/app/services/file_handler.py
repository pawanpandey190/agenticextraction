"""File upload and storage handling."""

import aiofiles
from pathlib import Path
from typing import BinaryIO

import structlog

from app.config import settings
from app.services.session_manager import session_manager

logger = structlog.get_logger(__name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}


class FileHandler:
    """Handles file uploads and storage."""

    def __init__(self):
        """Initialize the file handler."""
        self._max_size = settings.max_upload_size_mb * 1024 * 1024  # Convert to bytes

    def is_allowed_file(self, filename: str) -> bool:
        """Check if a file type is allowed.

        Args:
            filename: Name of the file.

        Returns:
            True if allowed, False otherwise.
        """
        suffix = Path(filename).suffix.lower()
        return suffix in ALLOWED_EXTENSIONS

    async def save_uploaded_file(
        self,
        session_id: str,
        filename: str,
        content: bytes,
    ) -> Path:
        """Save an uploaded file to the session directory.

        Args:
            session_id: Session identifier.
            filename: Original filename.
            content: File content as bytes.

        Returns:
            Path to the saved file.

        Raises:
            ValueError: If file type not allowed or file too large.
            FileNotFoundError: If session not found.
        """
        if not self.is_allowed_file(filename):
            raise ValueError(f"File type not allowed: {filename}")

        if len(content) > self._max_size:
            raise ValueError(f"File too large: {len(content)} bytes (max {self._max_size})")

        upload_dir = session_manager.get_upload_dir(session_id)
        if not upload_dir:
            raise FileNotFoundError(f"Session not found: {session_id}")

        # Sanitize filename
        safe_filename = Path(filename).name
        file_path = upload_dir / safe_filename

        # Handle duplicate filenames
        counter = 1
        original_stem = file_path.stem
        while file_path.exists():
            file_path = upload_dir / f"{original_stem}_{counter}{file_path.suffix}"
            counter += 1

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        logger.info(
            "file_uploaded",
            session_id=session_id,
            filename=safe_filename,
            size=len(content),
        )

        return file_path

    def list_uploaded_files(self, session_id: str) -> list[str]:
        """List all uploaded files for a session.

        Args:
            session_id: Session identifier.

        Returns:
            List of filenames.
        """
        upload_dir = session_manager.get_upload_dir(session_id)
        if not upload_dir or not upload_dir.exists():
            return []

        return [
            f.name for f in upload_dir.iterdir()
            if f.is_file() and self.is_allowed_file(f.name)
        ]

    def delete_file(self, session_id: str, filename: str) -> bool:
        """Delete an uploaded file.

        Args:
            session_id: Session identifier.
            filename: Name of file to delete.

        Returns:
            True if deleted, False if not found.
        """
        upload_dir = session_manager.get_upload_dir(session_id)
        if not upload_dir:
            return False

        file_path = upload_dir / filename
        if file_path.exists():
            file_path.unlink()
            logger.info("file_deleted", session_id=session_id, filename=filename)
            return True
        return False

    def get_result_file(self, session_id: str, filename: str) -> Path | None:
        """Get a result file path.

        Args:
            session_id: Session identifier.
            filename: Result filename (e.g., 'analysis_result.json').

        Returns:
            Path to the file if it exists, None otherwise.
        """
        output_dir = session_manager.get_output_dir(session_id)
        if not output_dir:
            return None

        file_path = output_dir / filename
        if file_path.exists():
            return file_path
        return None

    def extract_student_folders(
        self,
        files: list[tuple[str, bytes]],
    ) -> dict[str, list[tuple[str, bytes]]]:
        """Extract student folders from uploaded files.

        Args:
            files: List of (filename, content) tuples.

        Returns:
            Dictionary mapping student names to their files.
            Format: {student_name: [(filename, content), ...]}
        """
        student_folders: dict[str, list[tuple[str, bytes]]] = {}

        # First pass: detect if we have a parent folder structure
        # by checking if all files share a common parent folder
        all_paths = [filename.split("/") for filename, _ in files if not filename.split("/")[-1].startswith('.')]
        
        # Check if all paths have at least 2 levels (parent/student/file.pdf)
        has_parent_folder = all(len(parts) >= 3 for parts in all_paths if len(parts) > 1)
        
        if has_parent_folder and all_paths:
            # Check if they all share the same parent folder
            parent_folders = set(parts[0] for parts in all_paths if len(parts) >= 3)
            if len(parent_folders) == 1:
                # All files share the same parent folder, use second level as student name
                logger.info("detected_parent_folder_structure", parent_folder=list(parent_folders)[0])
                folder_offset = 1  # Skip the parent folder, use second level as student name
            else:
                folder_offset = 0  # Use first level as student name
        else:
            folder_offset = 0  # Use first level as student name

        for filename, content in files:
            # Skip hidden files and system files
            base_filename = filename.split("/")[-1]  # Get just the filename
            if base_filename.startswith('.') or base_filename.startswith('__'):
                logger.debug("skipping_hidden_file", filename=filename)
                continue

            # Parse folder structure from filename
            # Expected formats:
            # - "parent/student_name/document.pdf" (with parent folder)
            # - "student_name/document.pdf" (direct student folder)
            # - "document.pdf" (single file)
            parts = filename.split("/")
            
            if len(parts) > folder_offset + 1:
                # Has folder structure
                student_name = parts[folder_offset]  # Use appropriate level based on structure
                doc_filename = parts[-1]  # Last part is the actual filename
            else:
                # Single file or not enough folder depth, treat as single student
                student_name = "Student_1"
                doc_filename = parts[-1] if parts else filename

            # Initialize student folder if not exists
            if student_name not in student_folders:
                student_folders[student_name] = []

            # Add file to student's folder
            student_folders[student_name].append((doc_filename, content))

        logger.info(
            "student_folders_extracted",
            total_students=len(student_folders),
            students=list(student_folders.keys()),
        )

        return student_folders

    def validate_student_folder(
        self,
        files: list[tuple[str, bytes]],
    ) -> tuple[bool, str]:
        """Validate if folder contains valid documents.

        Args:
            files: List of (filename, content) tuples for a student.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not files:
            return False, "No files found in folder"

        # Filter out hidden files and system files
        valid_files = [
            (filename, content) 
            for filename, content in files 
            if not filename.startswith('.') and not filename.startswith('__')
        ]

        if not valid_files:
            return False, "No valid documents found (only hidden/system files)"

        # Check if all valid files have allowed extensions
        for filename, content in valid_files:
            if not self.is_allowed_file(filename):
                return False, f"Invalid file type: {filename}"

            # Check file size
            if len(content) > self._max_size:
                return False, f"File too large: {filename}"

        return True, ""

    def get_document_path(self, session_id: str, filename: str) -> Path | None:
        """Get path to an uploaded document for viewing.

        Args:
            session_id: Session identifier.
            filename: Document filename.

        Returns:
            Path to the document if it exists, None otherwise.
        """
        upload_dir = session_manager.get_upload_dir(session_id)
        if not upload_dir:
            return None

        file_path = upload_dir / filename
        if file_path.exists() and self.is_allowed_file(filename):
            return file_path
        return None

    def get_uploaded_documents(self, session_id: str) -> list[dict]:
        """Get list of uploaded documents with metadata.

        Args:
            session_id: Session identifier.

        Returns:
            List of document metadata dictionaries.
            Format: [{filename, size, type}, ...]
        """
        upload_dir = session_manager.get_upload_dir(session_id)
        if not upload_dir or not upload_dir.exists():
            return []

        # MIME type mapping
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".tif": "image/tiff",
        }

        documents = []
        for file_path in upload_dir.iterdir():
            if file_path.is_file() and self.is_allowed_file(file_path.name):
                ext = file_path.suffix.lower()
                documents.append({
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "type": mime_types.get(ext, "application/octet-stream"),
                })

        return documents


# Global file handler instance
file_handler = FileHandler()
