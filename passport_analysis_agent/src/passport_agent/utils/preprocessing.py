"""Image preprocessing utilities for passport documents."""

import numpy as np
from PIL import Image

from .exceptions import PreprocessingError


def auto_rotate(image: Image.Image) -> Image.Image:
    """Auto-rotate image based on EXIF orientation.

    Args:
        image: PIL Image object

    Returns:
        Rotated image if EXIF orientation found, otherwise original
    """
    try:
        # Check for EXIF data
        exif = image.getexif()
        if exif:
            orientation = exif.get(274)  # 274 is the EXIF orientation tag
            if orientation:
                if orientation == 3:
                    return image.rotate(180, expand=True)
                elif orientation == 6:
                    return image.rotate(270, expand=True)
                elif orientation == 8:
                    return image.rotate(90, expand=True)
        return image
    except Exception:
        # If EXIF parsing fails, return original
        return image


def enhance_contrast(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """Enhance image contrast for better OCR.

    Args:
        image: PIL Image object
        factor: Contrast enhancement factor (1.0 = no change)

    Returns:
        Contrast-enhanced image
    """
    try:
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)
    except Exception as e:
        raise PreprocessingError(f"Failed to enhance contrast: {e}") from e


def convert_to_grayscale(image: Image.Image) -> Image.Image:
    """Convert image to grayscale.

    Args:
        image: PIL Image object

    Returns:
        Grayscale image
    """
    return image.convert("L")


def deskew_image(image: Image.Image, max_angle: float = 10.0) -> Image.Image:
    """Deskew image using OpenCV.

    This function detects and corrects slight rotation in document images.

    Args:
        image: PIL Image object
        max_angle: Maximum angle to correct (degrees)

    Returns:
        Deskewed image
    """
    try:
        import cv2

        # Convert PIL to numpy array
        if image.mode != "RGB":
            image = image.convert("RGB")
        img_array = np.array(image)

        # Convert to grayscale
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)

        # Detect lines using Hough transform
        lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

        if lines is None:
            return image

        # Calculate angles of detected lines
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = np.degrees(theta) - 90
            # Only consider angles within range
            if abs(angle) <= max_angle:
                angles.append(angle)

        if not angles:
            return image

        # Use median angle
        median_angle = np.median(angles)

        if abs(median_angle) < 0.5:  # Skip if angle is negligible
            return image

        # Rotate the image
        (h, w) = img_array.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated = cv2.warpAffine(
            img_array,
            rotation_matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE,
        )

        return Image.fromarray(rotated)

    except ImportError:
        # If OpenCV not available, return original
        return image
    except Exception as e:
        raise PreprocessingError(f"Failed to deskew image: {e}") from e


def sharpen_image(image: Image.Image, factor: float = 1.5) -> Image.Image:
    """Sharpen image for better text detection.

    Args:
        image: PIL Image object
        factor: Sharpness factor (1.0 = no change)

    Returns:
        Sharpened image
    """
    try:
        from PIL import ImageEnhance

        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)
    except Exception as e:
        raise PreprocessingError(f"Failed to sharpen image: {e}") from e


def preprocess_passport_image(
    image: Image.Image,
    deskew: bool = True,
    enhance: bool = True,
) -> Image.Image:
    """Apply full preprocessing pipeline to passport image.

    Args:
        image: PIL Image object
        deskew: Whether to apply deskewing
        enhance: Whether to enhance contrast

    Returns:
        Preprocessed image
    """
    # Auto-rotate based on EXIF
    result = auto_rotate(image)

    # Convert to RGB if needed
    if result.mode not in ("RGB", "L"):
        result = result.convert("RGB")

    # Deskew if requested
    if deskew:
        result = deskew_image(result)

    # Enhance contrast if requested
    if enhance:
        result = enhance_contrast(result, factor=1.3)
        result = sharpen_image(result, factor=1.2)

    return result
