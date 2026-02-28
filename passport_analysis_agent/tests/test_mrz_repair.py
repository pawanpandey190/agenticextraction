
import sys
import os

# Add the src directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from passport_agent.services.mrz_service import MRZService

def test_mrz_hallucinated_prefix():
    service = MRZService()
    
    # Case provided by user
    text = """
    P<CODMUZINGA<<KIYOMBO<<<<<<<<<<<<<<<<<<<<<<<
    P<09409112C0002045045IF2612052P01200003906<<
    """
    
    extracted = service.extract_mrz_lines(text)
    print(f"Extracted Lines:")
    for i, line in enumerate(extracted):
        print(f"Line {i+1}: {line} (Length: {len(line)})")
    
    if extracted and extracted[1].startswith("0940911"):
        print("SUCCESS: Hallucinated 'P<' prefix stripped from Line 2")
    else:
        print("FAILURE: Hallucinated prefix NOT stripped or lines wrong")

    # Verify parsing
    try:
        data = service.parse(extracted)
        print(f"Parsed Data: {data.first_name} {data.last_name}, Passport: {data.passport_number}")
    except Exception as e:
        print(f"Parsing failed: {e}")

if __name__ == "__main__":
    test_mrz_hallucinated_prefix()
