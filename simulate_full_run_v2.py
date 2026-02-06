import sys
from pathlib import Path
import os
import gc
import time
import base64
import io
from PIL import Image

# Add all agents to path
root = Path("/Users/pawanpandey/Documents/french_admission_workflow-main")
for agent_dir in ["passport_analysis_agent", "financial_document_agent", "education_credential_agent", "master_orchestrator_agent"]:
    p = root / agent_dir / "src"
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

def resize_image_if_needed(image: Image.Image, max_dimension: int = 2048) -> Image.Image:
    width, height = image.size
    if width <= max_dimension and height <= max_dimension:
        return image
    scale = min(max_dimension / width, max_dimension / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def encode_image_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def simulate_orchestrator():
    session_id = "c1cbf5ce-4584-4e0b-ac52-16bec442f0fc"
    upload_dir = Path(f"/tmp/document_analysis_ui/{session_id}/uploads")
    
    print("--- 1. Simulating Passport (1 doc) ---")
    from passport_agent.utils.pdf_utils import pdf_to_images as p_pdf
    p_images = p_pdf(upload_dir / "Passport.pdf")
    for img in p_images:
        resized = resize_image_if_needed(img)
        _ = encode_image_base64(resized)
    print(f"Passport processed.")
    p_images = None
    gc.collect()
    
    print("\n--- 2. Simulating Financial (16 pages) ---")
    from financial_agent.utils.pdf_utils import pdf_to_images as f_pdf
    f_images = f_pdf(upload_dir / "Bank Balance Statement.pdf")
    print(f"Financial rendered {len(f_images)} pages.")
    for img in f_images:
        resized = resize_image_if_needed(img)
        _ = encode_image_base64(resized)
    print("Financial processed.")
    f_images = None
    gc.collect()
    
    print("\n--- 3. Simulating Education (3 docs) ---")
    from education_agent.utils.pdf_utils import pdf_to_images as e_pdf
    
    edu_files = [
        "Bachelor Transcripts.pdf",
        "High School Certificate and Transcript.pdf",
        "Pre- High School Certificate and Transcript.pdf"
    ]
    
    for f in edu_files:
        print(f"Loading {f}...")
        e_images = e_pdf(upload_dir / f)
        print(f"Rendered {len(e_images)} pages. Resizing first page...")
        if e_images:
            resized = resize_image_if_needed(e_images[0])
            _ = encode_image_base64(resized)
        print(f"Success! {f} processed.")
        e_images = None
        gc.collect()

if __name__ == "__main__":
    try:
        simulate_orchestrator()
        print("\nSIMULATION COMPLETE - NO CRASH.")
    except Exception as e:
        print(f"\nSIMULATION FAILED: {e}")
        import traceback
        traceback.print_exc()
