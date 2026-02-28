"""MRZ detector pipeline stage."""

from PIL import Image, ImageEnhance
import io
import base64

from ...prompts.extraction import get_mrz_extraction_prompt
from ...prompts.system import MRZ_EXTRACTION_SYSTEM_PROMPT
from ...services.llm_service import LLMService
from ...utils.image_utils import encode_image_base64
from ..base import PipelineContext, PipelineStage


class MRZDetectorStage(PipelineStage):
    """Stage 4: Detect and extract raw MRZ text from image."""

    def __init__(self, settings, llm_service: LLMService | None = None) -> None:
        """Initialize the MRZ detector stage.

        Args:
            settings: Application settings
            llm_service: Optional LLM service instance
        """
        super().__init__(settings)
        self.llm_service = llm_service or LLMService(settings)

    @property
    def name(self) -> str:
        return "MRZDetector"

    def process(self, context: PipelineContext) -> PipelineContext:
        """Detect and extract MRZ text from passport image.

        Uses Claude Vision to locate and read the MRZ zone.

        Args:
            context: Pipeline context

        Returns:
            Updated context with raw MRZ text

        Raises:
            ExtractionError: If MRZ detection fails
        """
        if not context.preprocessed_images:
            context.add_warning("No preprocessed images for MRZ detection")
            return context

        # Try to find MRZ in any of the pages (especially for IDs where it's on the back)
        for i, (image_base64, mime_type) in enumerate(context.preprocessed_images):
            page_num = i + 1
            self.logger.info(f"Attempting MRZ detection on page {page_num}")
            
            try:
                # Extract MRZ text using Claude Vision
                mrz_text = self.llm_service.extract_from_image(
                    image_base64=image_base64,
                    mime_type=mime_type,
                    system_prompt=MRZ_EXTRACTION_SYSTEM_PROMPT,
                    extraction_prompt=get_mrz_extraction_prompt(),
                )

                # Clean the extracted text
                cleaned_mrz = self._clean_mrz_text(mrz_text)

                # If not found, poor quality, or too short, attempt targeted cropping
                is_suspicious = not cleaned_mrz or len(cleaned_mrz.replace("\n", "")) < 80 or "MRZ_NOT_FOUND" in mrz_text.upper()
                
                if is_suspicious:
                    self.logger.info(f"MRZ found on page {page_num} is suspicious or short (len={len(cleaned_mrz) if cleaned_mrz else 0}), attempting targeted crop")
                    cropped_base64, cropped_mime = self._crop_mrz_area(image_base64)
                    
                    if cropped_base64:
                        retry_mrz_text = self.llm_service.extract_from_image(
                            image_base64=cropped_base64,
                            mime_type=cropped_mime,
                            system_prompt=MRZ_EXTRACTION_SYSTEM_PROMPT,
                            extraction_prompt=get_mrz_extraction_prompt(),
                        )
                        retry_cleaned = self._clean_mrz_text(retry_mrz_text)
                        
                        # Keep the better one (longer/more structured)
                        if retry_cleaned and len(retry_cleaned) >= (len(cleaned_mrz) if cleaned_mrz else 0):
                            self.logger.info(f"Targeted crop improved MRZ extraction on page {page_num}")
                            cleaned_mrz = retry_cleaned
                            mrz_text = retry_mrz_text
                        else:
                            self.logger.info(f"Targeted crop did not improve MRZ, keeping previous")

                if cleaned_mrz:
                    context.mrz_raw_text = cleaned_mrz
                    context.set_stage_result(
                        self.name,
                        {
                            "mrz_found": True,
                            "page_number": page_num,
                            "text_length": len(cleaned_mrz),
                            "method": "cropped" if not self._clean_mrz_text(mrz_text) else "full"
                        },
                    )
                    self.logger.info(f"MRZ text detected on page {page_num}", length=len(cleaned_mrz))
                    return context
                
            except Exception as e:
                self.logger.warning(f"MRZ detection failed on page {page_num}", error=str(e))
                continue

        # If we get here, no MRZ was found on any page
        context.add_warning("No MRZ text detected on any page")
        context.set_stage_result(self.name, {"mrz_found": False})
        self.logger.warning("No MRZ detected on any page")
        return context

    def _clean_mrz_text(self, text: str) -> str:
        """Clean extracted MRZ text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned MRZ text
        """
        if not text:
            return ""

        # Remove common OCR noise characters but keep MRZ characters
        # MRZ uses A-Z, 0-9, and '<'
        raw_lines = text.strip().split("\n")
        cleaned_lines = []
        
        for line in raw_lines:
            # Basic cleanup
            cleaned = line.strip().upper().replace(" ", "")
            
            # Support joined lines (e.g. 88 chars for TD3, 60 or 90 for TD1)
            if len(cleaned) >= 60 and "P<" in cleaned:
                # Likely 2x44 joined
                mid = len(cleaned) // 2
                cleaned_lines.append(cleaned[:mid])
                cleaned_lines.append(cleaned[mid:])
            elif len(cleaned) >= 80:
                # Likely 2x44 joined
                cleaned_lines.append(cleaned[:44])
                cleaned_lines.append(cleaned[44:88])
            elif len(cleaned) >= 25:
                # Keep regular lines
                cleaned_lines.append(cleaned)

        return "\n".join(cleaned_lines)

    def _crop_mrz_area(self, image_base64: str) -> tuple[str, str] | tuple[None, None]:
        """Crop the bottom portion of the image where MRZ typically resides.
        
        Also enhances contrast and sharpness to improve OCR.
        
        Args:
            image_base64: Base64 encoded image
            
        Returns:
            Tuple of (base64, mime_type) for the cropped/enhanced image
        """
        try:
            # Decode image
            img_data = base64.b64decode(image_base64)
            img = Image.open(io.BytesIO(img_data))
            
            width, height = img.size
            # Crop bottom 25% of the image
            top = int(height * 0.75)
            img_crop = img.crop((0, top, width, height))
            
            # Enhance image
            # Boost contrast
            enhancer = ImageEnhance.Contrast(img_crop)
            img_crop = enhancer.enhance(1.5)
            # Boost sharpness
            enhancer = ImageEnhance.Sharpness(img_crop)
            img_crop = enhancer.enhance(2.0)
            
            # Re-encode
            return encode_image_base64(img_crop)
            
        except Exception as e:
            self.logger.warning("Image cropping failed", error=str(e))
            return None, None
