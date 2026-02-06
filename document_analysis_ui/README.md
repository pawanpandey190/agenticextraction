# Document Analysis UI

A web UI for the Document Analysis Agents that provides:
- Document upload with drag-and-drop
- Real-time processing progress via SSE
- Tabbed report view for analysis results

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────────┐
│   React Frontend    │     │   FastAPI Backend   │     │   Master Orchestrator   │
│                     │     │                     │     │                         │
│ • Upload Page       │     │ • /api/sessions     │     │ • DocumentScanner       │
│ • Progress View     │◄SSE─│ • /api/progress     │────►│ • DocumentClassifier    │
│ • Report Tabs       │     │ • /api/results      │     │ • AgentDispatcher       │
│   - Passport        │     │                     │     │   ├─ PassportAdapter    │
│   - Financial       │     └─────────────────────┘     │   ├─ FinancialAdapter   │
│   - Education       │              │                  │   └─ EducationAdapter   │
│   - CrossValidation │              ▼                  │ • ResultNormalizer      │
│   - Metadata        │     ┌─────────────────────┐     │ • CrossValidator        │
└─────────────────────┘     │ /tmp/sessions/{id}/ │     │ • OutputGenerator       │
                            │ • uploads/          │     └─────────────────────────┘
                            │ • output/           │
                            └─────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI |
| Frontend | React + TypeScript |
| Styling | Tailwind CSS |
| Progress | Server-Sent Events (SSE) |

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run the server
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The UI will be available at http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/sessions` | Create new processing session |
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/{id}` | Get session details |
| DELETE | `/api/sessions/{id}` | Delete session |
| POST | `/api/sessions/{id}/documents` | Upload documents |
| GET | `/api/sessions/{id}/documents` | List uploaded documents |
| DELETE | `/api/sessions/{id}/documents/{filename}` | Delete a document |
| POST | `/api/sessions/{id}/process` | Start processing |
| GET | `/api/sessions/{id}/progress` | SSE stream for progress |
| GET | `/api/sessions/{id}/result` | Get analysis result |
| GET | `/api/sessions/{id}/download/json` | Download JSON result |
| GET | `/api/sessions/{id}/download/excel` | Download Excel result |

## Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DAU_HOST | 0.0.0.0 | Server host |
| DAU_PORT | 8000 | Server port |
| DAU_SESSION_BASE_DIR | /tmp/document_analysis_ui | Session storage path |
| DAU_SESSION_EXPIRY_HOURS | 24 | Session expiry time |
| DAU_MAX_UPLOAD_SIZE_MB | 50 | Max upload size per file |

## Report Tabs

| Tab | Fields Displayed |
|-----|------------------|
| **Passport** | first_name, last_name, date_of_birth, passport_number, issuing_country, issue_date, expiry_date, MRZ data, accuracy_score |
| **Financial** | document_type, account_holder_name, bank_name, base_currency, amount_original, amount_eur, worthiness_status, remarks |
| **Education** | highest_qualification, institution, country, student_name, final_grade_original, french_equivalent_grade_0_20, validation_status, remarks |
| **Cross-Validation** | name_match, name_match_score, dob_match, remarks |
| **Metadata** | total_documents_scanned, documents_by_category, processing_errors, processing_warnings, processing_time_seconds |

## Development

### Running Tests

Backend:
```bash
cd backend
pytest tests/
```

### Project Structure

```
document_analysis_ui/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Settings
│   │   ├── models/                 # Pydantic models
│   │   ├── routers/                # API routes
│   │   └── services/               # Business logic
│   ├── pyproject.toml
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── hooks/                  # Custom hooks
│   │   ├── services/               # API client
│   │   ├── pages/                  # Page components
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── README.md
```
