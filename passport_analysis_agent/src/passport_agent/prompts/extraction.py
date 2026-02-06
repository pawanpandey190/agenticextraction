"""Extraction prompts for passport data."""


def get_visual_extraction_prompt() -> str:
    """Get the prompt for visual passport data extraction.

    Returns:
        Extraction prompt string
    """
    return """Analyze this passport image and extract the following information from the Visual Inspection Zone (VIZ):

1. first_name: Given name(s) as shown on passport (uppercase)
2. last_name: Surname/family name as shown (uppercase)
3. date_of_birth: In YYYY-MM-DD format
4. passport_number: The document number
5. issuing_country: 3-letter ICAO country code
6. nationality: 3-letter ICAO country code
7. passport_issue_date: In YYYY-MM-DD format (if visible)
8. passport_expiry_date: In YYYY-MM-DD format
9. sex: M for Male, F for Female, X for Unspecified
10. place_of_birth: City/country of birth (if visible)
11. confidence: Your confidence score (0.0-1.0) based on image quality

Return the data as a JSON object with these exact field names.
For any field that is not visible or unclear, use null.

Example response:
{
  "first_name": "JOHN WILLIAM",
  "last_name": "SMITH",
  "date_of_birth": "1985-06-15",
  "passport_number": "123456789",
  "issuing_country": "USA",
  "nationality": "USA",
  "passport_issue_date": "2020-01-15",
  "passport_expiry_date": "2030-01-14",
  "sex": "M",
  "place_of_birth": "NEW YORK",
  "confidence": 0.95
}"""


def get_mrz_extraction_prompt() -> str:
    """Get the prompt for MRZ extraction.

    Returns:
        MRZ extraction prompt string
    """
    return """Extract the Machine Readable Zone (MRZ) from this passport image.

The MRZ consists of 2 lines at the bottom of the passport, each exactly 44 characters long.

TD3 Format (Passport):
Line 1: P<ISSUING_COUNTRY + SURNAME<<GIVEN_NAMES<<<<<<<<<<<<<<<<<<
Line 2: PASSPORT_NUMBER + CHECK + NATIONALITY + DOB + CHECK + SEX + EXPIRY + CHECK + OPTIONAL + CHECK

Return ONLY the two MRZ lines, exactly as they appear:
- Line 1 on the first line
- Line 2 on the second line
- No additional text, formatting, or explanation

Use < for filler characters.
Use UPPERCASE letters only.
Each line must be exactly 44 characters.

If the MRZ is not visible or readable, respond with: "MRZ_NOT_FOUND"

Example output:
P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
L898902C36UTO7408122F1204159<<<<<<<<<<<<<<06"""


def get_mrz_verification_prompt(mrz_line1: str, mrz_line2: str) -> str:
    """Get the prompt for MRZ verification.

    Args:
        mrz_line1: First MRZ line
        mrz_line2: Second MRZ line

    Returns:
        Verification prompt string
    """
    return f"""Verify the following MRZ lines extracted from a passport:

Line 1: {mrz_line1}
Line 2: {mrz_line2}

Check for:
1. Each line is exactly 44 characters
2. Only valid characters (A-Z, 0-9, <)
3. Line 1 starts with P or P<
4. Proper structure and formatting

If there are obvious OCR errors, suggest corrections.
Return the corrected lines or confirm they are correct."""
