# Financial Document Analysis Agent

A production-grade Python agent that reads banking documents (PDF, JPEG, PNG), extracts text via OCR, classifies documents, extracts financial data, converts currencies to EUR, and evaluates financial worthiness.

## Features

- **Multi-format Support**: PDF, JPEG, PNG document processing
- **Intelligent OCR**: Claude Vision API with Tesseract fallback
- **Document Classification**: Automatic detection of bank statements, letters, certificates
- **Financial Extraction**: Account holder, bank, balances, dates, currency
- **Currency Conversion**: Real-time EUR conversion via Frankfurter API (ECB rates)
- **Worthiness Evaluation**: Configurable threshold-based financial assessment

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd financial_document_agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# For OCR fallback support
pip install -e ".[ocr-fallback]"

# For development
pip install -e ".[dev]"
```

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required environment variables:
- `FA_ANTHROPIC_API_KEY`: Your Anthropic API key

## Usage

### CLI

```bash
# Basic usage
financial-agent --file document.pdf

# With custom threshold
financial-agent --file statement.pdf --threshold 15000

# Specify output format
financial-agent --file letter.png --output result.json
```

### Python API

```python
from financial_agent.pipeline.orchestrator import PipelineOrchestrator
from financial_agent.config.settings import Settings

settings = Settings()
orchestrator = PipelineOrchestrator(settings)
result = orchestrator.process("path/to/document.pdf")
print(result.model_dump_json(indent=2))
```

## Output Schema

```json
{
  "document_type": "BANK_STATEMENT",
  "account_holder": "John Doe",
  "bank_name": "Example Bank",
  "account_identifier": "DE89370400440532013000",
  "statement_period": {
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  },
  "currency_detected": "EUR",
  "base_currency_confidence": "HIGH",
  "balances": {
    "opening_balance": {"amount": 5000.00, "currency": "EUR"},
    "closing_balance": {"amount": 12500.00, "currency": "EUR"},
    "average_balance": {"amount": 8750.00, "currency": "EUR"}
  },
  "converted_to_eur": {
    "amount_eur": 8750.00,
    "conversion_basis": "average_balance"
  },
  "account_consistency": {
    "status": "CONSISTENT",
    "flags": []
  },
  "financial_worthiness": {
    "threshold_eur": 10000.00,
    "decision": "NOT_WORTHY",
    "reason": "Average balance 8750.00 EUR is below threshold of 10000.00 EUR"
  },
  "confidence_score": 0.95
}
```

## Architecture

```
Input (PDF/PNG/JPEG)
        │
        ▼
┌───────────────────┐
│  Document Loader  │ → Detect type, convert PDF to images
└───────────────────┘
        │
        ▼
┌───────────────────┐
│   OCR Processor   │ → Extract text via Claude Vision
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    Classifier     │ → BANK_STATEMENT | BANK_LETTER | CERTIFICATE | UNKNOWN
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    Extractor      │ → Account holder, bank, balances, dates, currency
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Currency Converter│ → Convert all amounts to EUR
└───────────────────┘
        │
        ▼
┌───────────────────┐
│    Evaluator      │ → WORTHY | NOT_WORTHY | INCONCLUSIVE
└───────────────────┘
        │
        ▼
JSON Output (AnalysisResult)
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/financial_agent --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py
```

## License

MIT License
