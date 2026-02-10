"""Image processing utilities."""

import base64
import io

from PIL import Image

# Maximum dimension for images sent to Claude Vision
MAX_IMAGE_DIMENSION = 2048
# Maximum file size for base64 encoded images (in bytes)
MAX_BASE64_SIZE = 20 * 1024 * 1024  # 20MB


def resize_image_if_needed(
    image: Image.Image,
    max_dimension: int = MAX_IMAGE_DIMENSION,
) -> Image.Image:
    """Resize image if it exceeds the maximum dimension.

    Args:
        image: PIL Image object
        max_dimension: Maximum allowed dimension (width or height)

    Returns:
        Resized image if needed, otherwise original image
    """
    width, height = image.size

    if width <= max_dimension and height <= max_dimension:
        return image

    # Calculate scaling factor
    scale = min(max_dimension / width, max_dimension / height)
    new_width = int(width * scale)
    new_height = int(height * scale)

    # Use high-quality resampling
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def encode_image_base64(
    image: Image.Image,
    format: str = "JPEG",
    quality: int = 85,
    max_size: int = 2867 * 1024,  # 2.8MB target for raw bytes to stay very safely under 5MB base64
) -> tuple[str, str]:
    """Encode a PIL Image to base64 string with size management.

    Args:
        image: PIL Image object
        format: Output format (PNG or JPEG). Defaults to JPEG for size.
        quality: JPEG compression quality (1-100)
        max_size: Maximum raw byte size before reducing quality/resolution

    Returns:
        Tuple of (base64_string, mime_type)
    """
    # Resize if any dimension is too large for Claude
    print(f"DEBUG: Encoding image {image.size}, current size unknown")
    image = resize_image_if_needed(image)

    # Convert RGBA to RGB for JPEG
    if format.upper() == "JPEG" and image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background

    buffer = io.BytesIO()
    
    # Try saving with initial quality
    save_kwargs: dict = {"format": format}
    if format.upper() == "JPEG":
        save_kwargs["quality"] = quality
    
    image.save(buffer, **save_kwargs)
    
    # If still too large, iteratively reduce quality if JPEG
    if buffer.tell() > max_size and format.upper() == "JPEG":
        current_quality = quality
        while buffer.tell() > max_size and current_quality > 30:
            current_quality -= 10
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=current_quality)
            
    # Final backup: If still too large, resize iteratively
    if buffer.tell() > max_size:
        while buffer.tell() > max_size:
            # Reduce dimensions by 20% each step
            width, height = image.size
            if width < 100 or height < 100: break # Safety break
            image = image.resize((int(width * 0.8), int(height * 0.8)), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=75)
            print(f"DEBUG: Resized to {image.size}, new size: {buffer.tell()} bytes")

    buffer.seek(0)
    base64_data = base64.standard_b64encode(buffer.read()).decode("utf-8")
    mime_type = f"image/{format.lower()}"

    return base64_data, mime_type


def image_to_bytes(
    image: Image.Image,
    format: str = "PNG",
    quality: int = 95,
) -> bytes:
    """Convert PIL Image to bytes.

    Args:
        image: PIL Image object
        format: Output format (PNG or JPEG)
        quality: JPEG quality (1-100)

    Returns:
        Image bytes
    """
    buffer = io.BytesIO()

    # Convert RGBA to RGB for JPEG
    if format.upper() == "JPEG" and image.mode == "RGBA":
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])
        image = background

    save_kwargs: dict = {"format": format}
    if format.upper() == "JPEG":
        save_kwargs["quality"] = quality

    image.save(buffer, **save_kwargs)
    buffer.seek(0)

    return buffer.read()


def bytes_to_image(data: bytes) -> Image.Image:
    """Convert bytes to PIL Image.

    Args:
        data: Image bytes

    Returns:
        PIL Image object
    """
    buffer = io.BytesIO(data)
    return Image.open(buffer)


def get_image_dimensions(data: bytes) -> tuple[int, int]:
    """Get image dimensions from bytes.

    Args:
        data: Image bytes

    Returns:
        Tuple of (width, height)
    """
    image = bytes_to_image(data)
    return image.size
