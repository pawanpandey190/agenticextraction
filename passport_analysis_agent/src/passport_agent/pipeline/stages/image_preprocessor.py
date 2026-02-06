"""Image preprocessor pipeline stage."""

import base64
import io

from PIL import Image

from ...utils.image_utils import encode_image_base64
from ...utils.preprocessing import preprocess_passport_image
from ..base import PipelineContext, PipelineStage


class ImagePreprocessorStage(PipelineStage):
    """Stage 2: Preprocess images for better OCR/extraction."""

    @property
    def name(self) -> str:
        return "ImagePreprocessor"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Preprocess document images.

        Applies auto-rotation, deskewing, and contrast enhancement.

        Args:
            context: Pipeline context

        Returns:
            Updated context with preprocessed images

        Raises:
            PreprocessingError: If preprocessing fails
        """
        if context.document is None:
            raise ValueError("No document loaded")

        preprocessed_images: list[tuple[str, str]] = []

        for page in context.document.pages:
            # Decode base64 to PIL Image
            image_data = base64.b64decode(page.image_base64)
            image = Image.open(io.BytesIO(image_data))

            # Apply preprocessing
            processed = preprocess_passport_image(
                image,
                deskew=True,
                enhance=True,
            )

            # Encode back to base64
            base64_data, mime_type = encode_image_base64(processed, format="PNG")
            preprocessed_images.append((base64_data, mime_type))

            self.logger.debug(
                "Page preprocessed",
                page_number=page.page_number,
                original_size=(page.width, page.height),
                processed_size=processed.size,
            )

        context.preprocessed_images = preprocessed_images
        context.set_stage_result(
            self.name, {"images_processed": len(preprocessed_images)}
        )

        self.logger.info(
            "Images preprocessed",
            count=len(preprocessed_images),
        )

        return context
