# Education Credential Evaluation Agent

A production-grade AI agent to evaluate student education credentials from multiple document types (PDF, JPEG, JPG, PNG). The agent classifies documents, extracts qualification data, validates Bachelor's degree semesters, and converts grades to the French 0-20 scale.

## Features

- **Multi-Document Processing**: Process entire folders of education documents
- **Document Classification**: Automatically identify document types (degree certificates, transcripts, mark sheets)
- **Academic Level Detection**: Classify credentials as Secondary, Diploma, Bachelor, Master, or Doctorate
- **Grade Extraction**: Extract grades in various formats (percentage, GPA, letter grades)
- **Semester Validation**: Validate completeness of Bachelor's degree semester records
- **Grade Conversion**: Convert grades to French 0-20 scale using configurable conversion tables
- **Structured Output**: JSON output with detailed analysis results

## Installation

```bash
# Clone the repository
cd education_credential_agent

# Install in development mode
pip install -e ".[dev]"
```

## Configuration

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Required configuration:

```bash
EA_OPENAI_API_KEY=your-api-key-here
```

Optional configuration:

```bash
EA_LLM_MODEL=gpt-4o
EA_LLM_MAX_TOKENS=4096
EA_LLM_TEMPERATURE=0.0
EA_DEFAULT_BACHELOR_SEMESTERS=8
EA_MAX_FILE_SIZE_MB=50
EA_MAX_PDF_PAGES=100
EA_LOG_LEVEL=INFO
EA_LOG_FORMAT=json
```

## Usage

### Command Line

```bash
# Evaluate all documents in a folder
education-agent --folder ./student_docs --grade-table ./data/grade_tables/default_conversion_table.json

# With verbose output
education-agent --folder ./docs --grade-table ./tables.json --verbose

# Output to file
education-agent --folder ./docs --grade-table ./tables.json --output result.json

# Process specific files
education-agent --files degree.pdf transcript.pdf --grade-table ./tables.json
```

### Python API

```python
from education_agent.config.settings import get_settings
from education_agent.pipeline.orchestrator import PipelineOrchestrator

# Initialize
settings = get_settings()
orchestrator = PipelineOrchestrator(
    settings=settings,
    grade_table_path="./data/grade_tables/default_conversion_table.json"
)

# Process documents
result = orchestrator.process_folder("./student_docs")

# Access results
print(result.highest_qualification)
print(result.evaluation.grade_conversion.french_equivalent_0_20)
```

## Output Format

```json
{
  "documents_analyzed": [
    {
      "file_name": "degree.pdf",
      "document_type": "DEGREE_CERTIFICATE",
      "country": "IN",
      "institution": "University of Delhi",
      "qualification": "Bachelor of Technology",
      "grading_system": "PERCENTAGE"
    }
  ],
  "highest_qualification": {
    "level": "BACHELOR",
    "qualification_name": "Bachelor of Technology",
    "institution": "University of Delhi",
    "country": "IN",
    "status": "Completed"
  },
  "evaluation": {
    "bachelor_rules_applied": true,
    "semester_validation": {
      "status": "COMPLETE",
      "missing_semesters": []
    },
    "grade_conversion": {
      "conversion_source": "GRADE CONVERSION TABLES BY REGION",
      "original_grade": "75%",
      "original_scale": "PERCENTAGE",
      "french_equivalent_0_20": "14.5",
      "conversion_notes": "Converted using India percentage rules"
    }
  },
  "flags": []
}
```

## Grade Conversion Table

The agent uses a JSON/YAML configuration file for grade conversions. The default table includes:

- **India**: Percentage system (0-100%)
- **United States**: GPA 4.0 and letter grades
- **United Kingdom**: Honours classification (First, 2:1, 2:2, Third)
- **Germany**: 1.0-5.0 scale (1.0 is best)
- **France**: 0-20 scale (native)
- **China**: Percentage and letter grades
- **Australia**: HD, D, CR, P, F system
- **Canada**: Percentage and letter grades

### Custom Conversion Tables

Create a custom JSON file:

```json
{
  "version": "1.0",
  "countries": [
    {
      "country_code": "XX",
      "country_name": "Custom Country",
      "system_type": "percentage",
      "numeric_ranges": [
        {"min_value": 80, "max_value": 100, "french_min": 16, "french_max": 20},
        {"min_value": 60, "max_value": 79.99, "french_min": 12, "french_max": 15.99}
      ]
    }
  ],
  "default_percentage_ranges": [...]
}
```

## Semester Validation

For Bachelor's degrees, the agent validates semester completeness:

- **B.Tech/B.E.**: 8 semesters expected
- **B.Sc/B.A./B.Com**: 6 semesters expected
- **B.Arch**: 10 semesters expected

If semesters are missing, the final grade is not computed and a flag is raised.

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest --cov=education_agent
```

### Code Quality

```bash
# Linting
ruff check src/

# Type checking
mypy src/
```

## Project Structure

```
education_credential_agent/
├── pyproject.toml
├── README.md
├── .env.example
├── src/
│   └── education_agent/
│       ├── __init__.py
│       ├── main.py                  # CLI entry point
│       ├── config/                  # Configuration
│       ├── models/                  # Data models
│       ├── pipeline/                # Processing pipeline
│       ├── services/                # External services
│       ├── prompts/                 # LLM prompts
│       └── utils/                   # Utilities
├── tests/
│   ├── unit/
│   └── integration/
└── data/
    └── grade_tables/
```

## License

MIT
