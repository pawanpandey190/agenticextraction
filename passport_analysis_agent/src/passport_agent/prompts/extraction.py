"""Extraction prompts for passport data."""


def get_visual_extraction_prompt() -> str:
    """Get the prompt for visual passport data extraction.

    Returns:
        Extraction prompt string
    """
    return """Analyze this passport image and extract the following information from the Visual Inspection Zone (VIZ). 

STEP 1: VISUAL RISK ASSESSMENT
Before extracting data, identify if the image has any of the following:
- GLARE (white reflections obscuring text)
- BLUR (soft edges or unreadable fine print)
- SHADOWS (uneven lighting)
- SKEW (tilted document)

STEP 2: DATA EXTRACTION
1. first_name: Extract ALL given names exactly as they appear.
2. last_name: Extract the complete surname.
3. date_of_birth: In YYYY-MM-DD format.
4. passport_number: Document number from the VIZ.
5. issuing_country: 3-letter ICAO country code.
6. nationality: 3-letter ICAO country code.
7. passport_issue_date: In YYYY-MM-DD format.
8. passport_expiry_date: In YYYY-MM-DD format.
9. sex: M, F, or X.
10. place_of_birth: City/country.
11. confidence: 0.0-1.0 (Penalize heavily for Step 1 risks).
12. accuracy_score: 0-100 (90+ only for perfect scans).
13. is_passport: Boolean.
14. justification: Start with a 'Visual Quality' section listing any defects found in Step 1, then explain the score.

CRITICAL: If glare is present over a name or number, your accuracy_score MUST be below 70.

Return as a JSON object with these exact field names."""


def get_mrz_extraction_prompt() -> str:
    """Get the prompt for MRZ extraction.

    Returns:
        MRZ extraction prompt string
    """
    return """Extract the Machine Readable Zone (MRZ) from this ID or passport image.

The MRZ is the multi-line code at the bottom of the document. It usually follows one of these formats:
- TD1 (Identity Card): 3 lines, each 30 characters long.
- TD2 (ID/Visa): 2 lines, each 36 characters long.
- TD3 (Passport): 2 lines, each 44 characters long.

Return ONLY the raw MRZ lines, exactly as they appear:
- Line 1 on the first line
- Line 2 on the second line
- Line 3 on the third line (if applicable)
- No additional text, formatting, or explanation

Use < for filler characters.
Use UPPERCASE letters only.
Ensure each line has the correct character count (30, 36, or 44).

If the MRZ is not visible or readable, respond with: "MRZ_NOT_FOUND" """


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
