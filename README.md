# DocClassifier — Document Classification & Extraction API

A Django REST API prototype that automatically classifies EU worker-posting documents (payslips, contracts, invoices, identity documents, tax forms) and extracts key fields using a language model.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [API Reference](#api-reference)
4. [Configuration](#configuration)
5. [Local vs Remote LLM](#local-vs-remote-llm)
6. [Technical Choices](#technical-choices)
7. [Confidence Score Heuristic](#confidence-score-heuristic)
8. [Testing](#testing)
9. [Git Workflow](#git-workflow)
10. [AI Usage](#ai-usage)

---

## Quick Start

### Prerequisites

- Python ≥ 3.10
- `libmagic` system library
  - macOS: `brew install libmagic`
  - Ubuntu/Debian: `sudo apt-get install libmagic1`
  - Arch/Manjaro: `sudo pacman -S file`
- Ollama (for local LLM): https://ollama.com

### Setup with Make

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/docclassifier.git
cd docclassifier

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Full setup (install deps + create .env + run migrations)
make setup

# 4. Start Ollama in a separate terminal
make ollama-serve

# 5. Pull the model (first time only)
make ollama-pull

# 6. Start the API
make run
```

### Setup without Make

```bash
git clone https://github.com/YOUR_USERNAME/docclassifier.git
cd docclassifier

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env

python manage.py makemigrations documents
python manage.py migrate

# In a separate terminal:
ollama serve
ollama pull llama3.2

python manage.py runserver
```

The API is now available at `http://localhost:8000`.

### Available Make Commands

```bash
make help         # show all commands
make setup        # full first-time setup
make install      # pip install dependencies
make env          # create .env from .env.example
make migrate      # run database migrations
make run          # start Django dev server
make test         # run all tests
make ollama-serve # start Ollama server
make ollama-pull  # download llama3.2 model
```

### Docker (one command)

```bash
cp .env.example .env
docker-compose up
```

To use with local Ollama:
```bash
docker-compose --profile local up
# Then in another terminal:
docker exec <ollama_container> ollama pull llama3.2
```

---

## Project Structure

```
docclassifier/
├── config/                      # Django project configuration
│   ├── __init__.py
│   ├── settings.py              # All settings, reads from .env
│   ├── urls.py                  # Root URL routing
│   └── wsgi.py
│
├── documents/                   # Main Django application
│   ├── models.py                # ClassifiedDocument model
│   ├── views.py                 # APIViews: classify, detail, list
│   ├── serializers.py           # DRF serializers (detail + list)
│   ├── urls.py                  # URL patterns for documents app
│   ├── validators.py            # File format and size validation
│   ├── pipeline.py              # Orchestrator: extract → LLM → score → save
│   ├── confidence.py            # Heuristic confidence scoring logic
│   │
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── pdf_extractor.py     # PDF text extraction using pdfplumber
│   │   └── ocr_extractor.py     # Image OCR using EasyOCR
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py              # Abstract BaseLLMProvider (strategy pattern)
│   │   ├── prompts.py           # System prompt + user message builder
│   │   ├── openai_provider.py   # OpenAI GPT implementation
│   │   ├── ollama_provider.py   # Ollama local model implementation
│   │   └── factory.py          # Provider factory (reads LLM_PROVIDER env var)
│   │
│   └── tests/
│       ├── __init__.py
│       ├── fixtures.py          # Shared test helpers and fake data
│       ├── test_classify_view.py
│       ├── test_retrieval_views.py
│       ├── test_confidence.py
│       └── test_llm_providers.py
│
├── manage.py
├── requirements.txt
├── pytest.ini
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── .env.example                 # Template — copy to .env
└── .gitignore
```

### Key Design Decisions

**Strategy Pattern for LLM providers**: `BaseLLMProvider` is an abstract class defining the interface. `OpenAIProvider` and `OllamaProvider` are concrete implementations. `get_llm_provider()` in `factory.py` reads the `LLM_PROVIDER` environment variable and returns the correct instance. Switching providers requires zero code changes.

**Separation of concerns**: Each responsibility lives in its own module. `pipeline.py` is a thin orchestrator that calls validators, extractors, LLM, confidence scorer and persistence in sequence — nothing else.

**Single shared prompt**: `llm/prompts.py` centralises the system prompt, field schema, and category definitions. All providers use the same prompt, ensuring consistent classification behaviour regardless of which model is used.

**Lazy OCR loading**: The EasyOCR reader (~400 MB model) is initialised only on first use via a thread-safe singleton, preventing slow server startup.

---

## API Reference

### POST `/api/documents/classify/`

Classify one or more documents. Accepts up to 3 files per request.

**Request**: `multipart/form-data` with field name `files`.

```bash
# Single file
curl -X POST http://localhost:8000/api/documents/classify/ \
  -F "files=@busta_paga_marzo.pdf"

# Multiple files
curl -X POST http://localhost:8000/api/documents/classify/ \
  -F "files=@busta_paga_marzo.pdf" \
  -F "files=@contratto_lavoro.pdf"
```

**Response** `201 Created`:
```json
{
  "results": [
    {
      "id": "b7f3a1c2-7628-4e74-b2fc-d078c768d5d6",
      "filename": "busta_paga_marzo.pdf",
      "category": "payslip",
      "confidence": "high",
      "extracted_fields": {
        "employee_name": "Mario Rossi",
        "employer_name": "Arletti Partners SRL",
        "pay_period": "Marzo 2026",
        "gross_salary": "2,850.00 EUR",
        "net_salary": "2,015.00 EUR",
        "tax_withheld": "500.00 EUR"
      },
      "raw_text_preview": "CEDOLINO PAGA - Marzo 2026 | Dipendente: Mario Rossi | Qualifica: Impiegato...",
      "model_used": "ollama/llama3.2",
      "processing_time_ms": 3120,
      "created_at": "2026-03-03T10:30:00Z"
    }
  ]
}
```

**Error responses**:

| Status | Reason |
|--------|--------|
| `400` | No files uploaded |
| `400` | More than 3 files in one request |
| `400` | Invalid file format (not PDF/JPEG/PNG) |
| `400` | File exceeds 5 MB size limit |
| `503` | LLM provider unreachable or timed out |

---

### GET `/api/documents/{id}/`

Retrieve a previously classified document by its UUID.

```bash
curl http://localhost:8000/api/documents/b7f3a1c2-7628-4e74-b2fc-d078c768d5d6/
```

**Response** `200 OK` — full detail JSON (same schema as classify response).

**Response** `404 Not Found`:
```json
{"error": "Document 'b7f3a1c2-...' not found."}
```

---

### GET `/api/documents/`

List all classified documents. Supports optional query filters.

```bash
# All documents
curl http://localhost:8000/api/documents/

# Filter by category
curl "http://localhost:8000/api/documents/?category=payslip"

# Filter by confidence
curl "http://localhost:8000/api/documents/?confidence=high"

# Combined filter
curl "http://localhost:8000/api/documents/?category=invoice&confidence=medium"
```

Available categories: `identity_document`, `employment_contract`, `payslip`, `invoice`, `tax_form`, `other`

Available confidence values: `high`, `medium`, `low`

**Response** `200 OK`:
```json
{
  "count": 3,
  "results": [
    {
      "id": "b7f3a1c2-7628-4e74-b2fc-d078c768d5d6",
      "filename": "busta_paga_marzo.pdf",
      "category": "payslip",
      "confidence": "high",
      "created_at": "2026-03-03T10:30:00Z"
    }
  ]
}
```

---

## Configuration

All configuration is stored in `.env`. Copy `.env.example` to get started:

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | dev key | Django secret key — change in production |
| `DEBUG` | `true` | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hosts |
| `LLM_PROVIDER` | `ollama` | `ollama` or `openai` |
| `OPENAI_API_KEY` | — | Required only if `LLM_PROVIDER=openai` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Ollama model name |
| `LLM_TIMEOUT_SECONDS` | `30` | Max seconds per LLM request |

---

## Local vs Remote LLM

### Local — Ollama (default, free, no API key needed)

```bash
# 1. Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 2. Start Ollama server (keep this terminal open)
ollama serve

# 3. Pull a model
ollama pull llama3.2        # ~2 GB, recommended
# or for faster performance on low-end machines:
ollama pull llama3.2:1b     # ~600 MB, faster

# 4. Set in .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

> **Tip**: If requests time out, increase `LLM_TIMEOUT_SECONDS=120` or switch to `llama3.2:1b`.

---

### Remote — OpenAI (paid, fastest, most accurate)

```bash
# 1. Get API key from https://platform.openai.com/api-keys

# 2. Set in .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

Uses `gpt-4o-mini` — fast and cost-effective (~$0.001 per document).

---

## Technical Choices

### PDF Extraction — pdfplumber

| Library | Notes |
|---|---|
| **pdfplumber** ✅ chosen | Preserves table and column layout. Payslips and invoices have salary tables — pdfplumber extracts these more accurately. Higher-level API built on pdfminer. |
| PyMuPDF | Faster but returns less structured text. Better for plain narrative documents. |
| pdfminer | Lower-level engine pdfplumber is built on. More verbose API with no advantage here. |

**Trade-off**: pdfplumber is slower than PyMuPDF and cannot extract text from scanned PDFs (no text layer). Scanned documents must be submitted as images and processed via OCR.

---

### Image OCR — EasyOCR

| Library | Notes |
|---|---|
| **EasyOCR** ✅ chosen | Built-in Italian + English language support. Pure Python install via pip. Better accuracy on low-resolution and skewed scans common in HR documents. |
| Tesseract | Requires system-level installation and separate language data files per language. More fragile setup. |
| pytesseract | Python wrapper for Tesseract — inherits all the same drawbacks. |

**Trade-off**: EasyOCR downloads a ~400 MB neural model on first use. This is mitigated with a lazy singleton — the reader is initialised only when the first image is actually processed, not at server startup.

---

### LLM Prompt Design

The system prompt in `documents/llm/prompts.py` is designed to:

1. Set the task context: EU worker-posting compliance system
2. List all 6 document categories with both Italian and English keywords
3. Define the exact expected field schema for each category
4. Enforce **JSON-only output** — no markdown fences, no commentary
5. Instruct the model to set `null` for missing fields and never invent values
6. Normalise dates to ISO-8601 format where possible

The **filename** is included as a hint in every user message. For example `busta_paga_marzo.pdf` is a strong Italian-language signal for `payslip` even before the document content is read.

---

## Confidence Score Heuristic

The confidence score (`high` / `medium` / `low`) is computed deterministically by `documents/confidence.py` using three weighted signals:

| Signal | Weight | Logic |
|---|---|---|
| **Field completeness** | 60% | `non-null extracted fields / total expected fields` for the predicted category |
| **Text length** | 20% | ≥ 300 chars → full score; ≥ 100 chars → half score; < 100 chars → 0 |
| **Filename keyword match** | 20% | Filename contains a keyword strongly associated with the predicted category |

**Score → Confidence mapping**:

| Score | Level |
|---|---|
| ≥ 0.70 | `high` |
| ≥ 0.40 | `medium` |
| < 0.40 | `low` |

**Rationale**:
- **Field completeness (60%)** is the dominant signal. If the LLM extracted all expected fields, the document type is almost certainly correct.
- **Text length (20%)** guards against silent failures. Very short extracted text (< 100 chars) usually means the PDF extractor or OCR failed, making any classification unreliable.
- **Filename match (20%)** is a free, fast corroborating signal. `cedolino_marzo.pdf` strongly implies payslip; `scan_001.pdf` provides no information.

The expected field lists in `confidence.py` mirror the field schema in `prompts.py` exactly, so scoring and classification always agree on what fields are expected.

---

## Testing

```bash
# Run all tests
make test

# Run a specific file
pytest documents/tests/test_classify_view.py -v

# Run with coverage report
pip install pytest-cov
pytest --cov=documents --cov-report=term-missing
```

All external dependencies (OpenAI API, Ollama HTTP endpoint, PDF extractor, EasyOCR) are **fully mocked** in tests. No real API keys, no real files, and no running Ollama instance are needed to run the test suite.

### Test coverage

| File | Cases covered |
|---|---|
| `test_classify_view.py` | Single file happy path, multiple files happy path, no files → 400, too many files → 400, invalid extension → 400, file too large → 400, LLM unreachable → 503 |
| `test_retrieval_views.py` | GET existing document → 200, GET non-existent ID → 404, list all, filter by category, filter by confidence, combined filter |
| `test_confidence.py` | All fields present → high, no fields → low, `other` category neutral score, filename keyword boost |
| `test_llm_providers.py` | OpenAI success, connection error → LLMProviderError, missing API key → LLMProviderError, invalid JSON response → LLMProviderError, Ollama success, connection error → LLMProviderError, timeout → LLMProviderError, factory returns correct provider, unknown provider → ValueError |

---

## Git Workflow

This project follows a feature-branch strategy with Pull Requests into `main`.

### Branch strategy

| Branch | What it introduces |
|---|---|
| `feature/text-extraction` | PDF extraction (pdfplumber) + image OCR (EasyOCR) |
| `feature/llm-classification` | Strategy interface, OpenAI + Ollama providers, factory, shared prompt |
| `feature/api-endpoints` | Django model, serializers, views, URLs, pipeline, confidence scorer, validators |
| `feature/tests` | All test files with mocked external dependencies |

Each branch was merged into `main` via a Pull Request. No force-pushes were made on `main`.

### Commit conventions

```
feat:   new feature
fix:    bug fix
test:   test files
chore:  config, tooling, dependencies
docs:   documentation only
```

---

## AI Usage

### Tools used

- **Claude (claude.ai)** — architecture design, prompt engineering, boilerplate generation, README drafting
- **GitHub Copilot** — inline code completion during implementation

### Tasks where AI was used

- Generating the initial Django project structure and deciding which files to split
- Writing and iterating the LLM system prompt (multiple rounds)
- Generating mock patterns for test cases involving `APIConnectionError` and `requests.ConnectionError`
- Drafting the README structure

### Prompt iteration example

**Initial prompt:**
> "Write a Django REST API that classifies documents using an LLM and extracts fields"

The output was a single-file monolith with hardcoded API keys and no separation of concerns. **Discarded entirely.**

**Iterated prompt:**
> "I need a Django app with:
> (1) Strategy pattern for LLM providers selectable via LLM_PROVIDER env var — ollama and openai
> (2) Separate modules for PDF extraction, OCR, confidence scoring, and pipeline orchestration
> (3) The LLM prompt must enforce JSON-only output with a defined field schema per document category
> (4) No keys in code — all config via .env
> Show me the directory structure first, then implement each file separately."

This produced the modular architecture used in the project. The key iterations were specifying the **strategy pattern** explicitly, requiring **JSON-only output enforcement** in the prompt design, and breaking the request into parts rather than asking for everything at once.

### Where AI output was corrected or discarded

**Correction 1 — Confidence scoring**: The AI initially had the LLM return its own confidence score as part of the classification JSON. This was discarded because LLM self-reported confidence is not calibrated and cannot be independently audited. The scoring was replaced with a deterministic rule-based function in `confidence.py` that can be tuned and tested independently of the LLM.

**Correction 2 — File size validation test**: The AI-generated test mocked file size by patching an internal Django attribute. This was replaced with an actual oversized `SimpleUploadedFile` with real byte content, because the validator reads real byte counts from the file object — patching internals would not test the actual validation code path.

**Correction 3 — EasyOCR initialisation**: The AI placed `_reader = easyocr.Reader(["en", "it"])` at module level (executed on import). This caused a 10+ second delay every time the server started as the neural network model was loaded. It was refactored to a lazy singleton with a `threading.Lock`, so the model loads only when the first image file is actually processed during a request.
