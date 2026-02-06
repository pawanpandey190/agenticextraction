"""Classification prompts for document type and academic level detection."""

CLASSIFICATION_PROMPT = """Analyze this education document and classify it.

## Document Type Classification

Classify into one of these document types:
1. DEGREE_CERTIFICATE - Official certificate conferring a degree
2. TRANSCRIPT - Academic transcript showing courses and grades
3. MARK_SHEET - General mark sheet (not semester-specific)
4. DIPLOMA - Diploma certificate (non-degree qualification)
5. SEMESTER_MARK_SHEET - Mark sheet for a specific semester
6. CONSOLIDATED_MARK_SHEET - Combined mark sheet for all semesters
7. PROVISIONAL_CERTIFICATE - Temporary/provisional certificate
8. UNKNOWN - Cannot determine document type

## Academic Level Classification

Determine the academic level:
1. SECONDARY - High school / Secondary education
2. DIPLOMA - Diploma / Certificate programs (non-degree)
3. BACHELOR - Bachelor's degree (B.Tech, B.E., B.Sc., B.A., B.Com, BBA, BCA, etc.)
4. MASTER - Master's degree (M.Tech, M.E., M.Sc., M.A., MBA, MCA, etc.)
5. DOCTORATE - PhD / Doctoral degree
6. TRANSCRIPT - Academic transcript (determine level from content)
7. OTHER - Cannot determine academic level

## Key Indicators to Look For:
- Document title and headings
- Institution name and type
- Degree/qualification name mentioned
- Semester number (if present)
- Terms like "provisional", "final", "consolidated"
- Official stamps, signatures, registrar mentions

## Important Guidance for Transcripts vs Consolidated Mark Sheets:
- If a TRANSCRIPT contains a cumulative GPA/CGPA or final aggregate grade,
  and lists courses/grades for multiple years/semesters, classify as CONSOLIDATED_MARK_SHEET
- Individual SEMESTER_MARK_SHEET documents only show grades for ONE semester
- Transcripts from international universities (non-Indian) are typically consolidated records
  that contain the complete academic history and should be classified as CONSOLIDATED_MARK_SHEET
- Only classify as TRANSCRIPT if it appears to be a partial record or does not contain
  a final cumulative grade

Return your classification as JSON:
{
    "document_type": "DEGREE_CERTIFICATE" | "TRANSCRIPT" | "MARK_SHEET" | "DIPLOMA" | "SEMESTER_MARK_SHEET" | "CONSOLIDATED_MARK_SHEET" | "PROVISIONAL_CERTIFICATE" | "UNKNOWN",
    "academic_level": "SECONDARY" | "DIPLOMA" | "BACHELOR" | "MASTER" | "DOCTORATE" | "TRANSCRIPT" | "OTHER",
    "semester_number": null | 1-12,
    "is_provisional": true | false,
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of classification decision",
    "key_indicators": ["list", "of", "indicators", "found"]
}

Analyze the document text provided and classify it accurately."""

CLASSIFICATION_WITH_IMAGE_PROMPT = """Analyze this education document (both the image and extracted text) and classify it.

Consider:
- Visual layout and formatting
- Letterhead, logos, and official seals
- Document structure and organization
- Textual content and headings

## Document Type Classification

Classify into one of these document types:
1. DEGREE_CERTIFICATE - Official certificate conferring a degree
2. TRANSCRIPT - Academic transcript showing courses and grades
3. MARK_SHEET - General mark sheet (not semester-specific)
4. DIPLOMA - Diploma certificate (non-degree qualification)
5. SEMESTER_MARK_SHEET - Mark sheet for a specific semester
6. CONSOLIDATED_MARK_SHEET - Combined mark sheet for all semesters
7. PROVISIONAL_CERTIFICATE - Temporary/provisional certificate
8. UNKNOWN - Cannot determine document type

## Academic Level Classification

Determine the academic level:
1. SECONDARY - High school / Secondary education
2. DIPLOMA - Diploma / Certificate programs (non-degree)
3. BACHELOR - Bachelor's degree (B.Tech, B.E., B.Sc., B.A., B.Com, BBA, BCA, etc.)
4. MASTER - Master's degree (M.Tech, M.E., M.Sc., M.A., MBA, MCA, etc.)
5. DOCTORATE - PhD / Doctoral degree
6. TRANSCRIPT - Academic transcript (determine level from content)
7. OTHER - Cannot determine academic level

## Important Guidance for Transcripts vs Consolidated Mark Sheets:
- If a TRANSCRIPT contains a cumulative GPA/CGPA or final aggregate grade,
  and lists courses/grades for multiple years/semesters, classify as CONSOLIDATED_MARK_SHEET
- Individual SEMESTER_MARK_SHEET documents only show grades for ONE semester
- Transcripts from international universities (non-Indian) are typically consolidated records
  that contain the complete academic history and should be classified as CONSOLIDATED_MARK_SHEET
- Only classify as TRANSCRIPT if it appears to be a partial record or does not contain
  a final cumulative grade

Return your classification as JSON:
{
    "document_type": "DEGREE_CERTIFICATE" | "TRANSCRIPT" | "MARK_SHEET" | "DIPLOMA" | "SEMESTER_MARK_SHEET" | "CONSOLIDATED_MARK_SHEET" | "PROVISIONAL_CERTIFICATE" | "UNKNOWN",
    "academic_level": "SECONDARY" | "DIPLOMA" | "BACHELOR" | "MASTER" | "DOCTORATE" | "TRANSCRIPT" | "OTHER",
    "semester_number": null | 1-12,
    "is_provisional": true | false,
    "confidence": 0.0 to 1.0,
    "reasoning": "Brief explanation of classification decision",
    "key_indicators": ["list", "of", "indicators", "found"]
}"""
