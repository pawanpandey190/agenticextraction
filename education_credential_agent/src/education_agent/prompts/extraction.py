"""Extraction prompts for credential data extraction."""

EXTRACTION_PROMPT = """Extract all relevant credential information from this education document.

## Required Information to Extract:

### Institution Information
- institution_name: Full name of the educational institution
- institution_country: Country code (ISO 3166-1 alpha-2, e.g., "IN", "US", "GB")
- institution_city: City where institution is located
- institution_state: State or province

### Student Information
- student_name: Full name of the student
- student_id: Roll number, registration number, or student ID

### Qualification Information
- qualification_name: Name of the degree/qualification (e.g., "Bachelor of Technology", "Master of Science")
- specialization: Major, branch, or specialization (e.g., "Computer Science", "Mechanical Engineering")

### Grade Information
- grading_system: One of "PERCENTAGE", "GPA_4", "GPA_10", "LETTER_GRADE", "FRENCH_20", "UK_HONORS", "GERMAN_5", "OTHER"
- final_grade_value: The grade/marks/GPA as shown on document
- final_grade_numeric: Numeric value if applicable
- max_possible_grade: Maximum possible grade in the system (e.g., 100 for percentage, 4.0 for GPA)

### Semester Information (if this is a semester mark sheet)
- semester_number: Semester number (1, 2, 3, etc.)
- academic_year: Academic year (e.g., "2020-2021")
- semester_grade: Grade for this semester

### Consolidated Mark Sheet Handling
If this document shows grades for multiple semesters/years (consolidated mark sheet):
1. FIRST look for an explicitly stated overall/final/aggregate grade:
   - Labels: "Final Grade", "Overall Percentage", "Aggregate", "CGPA", "Cumulative GPA", etc.
2. If NO explicit final grade exists, calculate the simple average of all semester grades
3. Always provide a single numeric_value representing overall academic performance
4. Note in extraction_notes if the value was calculated (e.g., "Average of 6 semesters")

Examples:
- Document shows "Final CGPA: 7.5" -> numeric_value: 7.5
- Document shows "Aggregate: 72%" -> numeric_value: 72
- Document shows only "Sem 1: 63%, Sem 2: 57%, Sem 3: 62%" -> numeric_value: 60.67 (average)

### Dates
- issue_date: Date the document was issued
- completion_date: Date of completion
- year_of_passing: Year of passing/graduation

### Document Status
- is_provisional: Whether this is a provisional certificate

## Grading System Detection Rules:
- If grades are in 0-100 range with % symbol -> PERCENTAGE
- If grades are in 0-4.0 range -> GPA_4
- If grades are in 0-10.0 range (common in India) -> GPA_10
- If grades are A, B, C, D, F or A+, A-, B+, etc. -> LETTER_GRADE
- If grades are First, 2:1, 2:2, Third -> UK_HONORS
- If grades are in 1.0-5.0 range (1.0 best) -> GERMAN_5
- If grades are in 0-20 range -> FRENCH_20

Return your extraction as JSON:
{
    "institution": {
        "name": "string or null",
        "country": "2-letter code or null",
        "city": "string or null",
        "state": "string or null"
    },
    "student": {
        "name": "string or null",
        "id": "string or null"
    },
    "qualification": {
        "name": "string or null",
        "specialization": "string or null"
    },
    "grade": {
        "grading_system": "PERCENTAGE" | "GPA_4" | "GPA_10" | "LETTER_GRADE" | "FRENCH_20" | "UK_HONORS" | "GERMAN_5" | "OTHER",
        "original_value": "string as shown on document",
        "numeric_value": number or null,  # For consolidated sheets: MUST be a single aggregated value
        "max_possible": number or null
    },
    "semester": {
        "number": number or null,
        "academic_year": "string or null",
        "grade": "string or null"
    },
    "dates": {
        "issue_date": "string or null",
        "completion_date": "string or null",
        "year_of_passing": "string or null"
    },
    "is_provisional": true | false,
    "confidence": 0.0 to 1.0,
    "extraction_notes": "any notes about uncertain extractions"
}

Extract information accurately. If information is not present, use null. Do not guess or infer missing data."""
