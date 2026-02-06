# Passport Analysis Agent

AI-powered passport document analysis agent using OpenAI Vision. Extracts data from passport documents, parses MRZ zones, cross-validates fields, and provides accuracy scoring.

## Features

- **Visual Zone Extraction**: Uses OpenAI Vision to extract passport data from the Visual Inspection Zone (VIZ)
- **MRZ Parsing**: Detects and parses TD3 format Machine Readable Zone with ICAO 9303 checksum validation
- **Cross-Validation**: Compares visual data with MRZ data using fuzzy and exact matching
- **Accuracy Scoring**: Calculates confidence score (0-100) based on checksums, field matches, and OCR confidence

## Installation

```bash
# Clone the repository
cd passport_analysis_agent

# Install with pip
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `PA_OPENAI_API_KEY`: Your OpenAI API key

## Usage

### Command Line

```bash
# Analyze a single passport document
passport-agent /path/to/passport.pdf

# Analyze with JSON output
passport-agent /path/to/passport.png --output json

# Analyze all documents in a folder
passport-agent /path/to/documents/
```

### Python API

```python
from passport_agent.pipeline.orchestrator import PassportPipelineOrchestrator
from passport_agent.config.settings import get_settings

settings = get_settings()
orchestrator = PassportPipelineOrchestrator(settings)

result = orchestrator.process("/path/to/passport.pdf")
print(result.accuracy_score)
print(result.confidence_level)
```

## Output Format

```json
{
  "extracted_passport_data": {
    "first_name": "ANNA MARIA",
    "last_name": "ERIKSSON",
    "date_of_birth": "1974-08-12",
    "passport_number": "L898902C3",
    "issuing_country": "UTO",
    "passport_expiry_date": "2012-04-15",
    "sex": "F",
    "ocr_confidence": 0.95
  },
  "extracted_mrz_data": {
    "document_type": "P",
    "issuing_country": "UTO",
    "last_name": "ERIKSSON",
    "first_name": "ANNA MARIA",
    "passport_number": "L898902C3",
    "nationality": "UTO",
    "date_of_birth": "1974-08-12",
    "sex": "F",
    "expiry_date": "2012-04-15"
  },
  "field_comparison": {
    "first_name": "match",
    "last_name": "match",
    "date_of_birth": "match",
    "passport_number": "match",
    "sex": "match",
    "issuing_country": "match",
    "expiry_date": "match"
  },
  "mrz_checksum_validation": {
    "passport_number": true,
    "date_of_birth": true,
    "expiry_date": true,
    "composite": true
  },
  "accuracy_score": 95,
  "confidence_level": "HIGH",
  "processing_errors": []
}
```

## Pipeline Stages

1. **DocumentLoaderStage**: Validate file, detect type, convert PDF to images
2. **ImagePreprocessorStage**: Auto-rotate, deskew, enhance contrast
3. **VisualExtractorStage**: Extract VIZ fields using OpenAI Vision
4. **MRZDetectorStage**: Locate and extract raw MRZ text
5. **MRZParserStage**: Parse TD3 lines, validate all checksums
6. **CrossValidatorStage**: Compare visual vs MRZ with fuzzy/exact matching
7. **ScorerStage**: Calculate accuracy score (0-100), confidence level

## MRZ Format (TD3)

The agent supports TD3 format passports (88 characters, 2 lines of 44):

```
Line 1: P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<
Line 2: L898902C36UTO7408122F1204159<<<<<<<<<<<<<<06
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=passport_agent

# Run only unit tests
pytest tests/unit/
```

## License

MIT License
