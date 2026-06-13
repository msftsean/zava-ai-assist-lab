# Copilot Instructions — AI Assist Lab

## Build & Run

```bash
# Install dependencies
pip install -r app/requirements.txt

# Run the FastAPI app
uvicorn app.main:app --reload --port 8000

# Run with Docker (includes PostgreSQL + pgvector)
docker compose up -d
```

## Testing

```bash
# Unit tests (default — no Azure services needed)
pytest

# Single test file
pytest tests/unit/test_rag.py

# Single test by name
pytest tests/unit/test_rag.py -k "test_rag_query_basic"

# Integration tests (mocked Azure services)
pytest -m integration

# All tests (override default marker filter)
pytest -m ""

# Eval harness (mock mode — no Azure credentials required)
python -m evals.harness.eval_runner --mock
```

`pytest.ini` defaults to `-m "not integration"`, so `pytest` alone runs only unit tests.

## Architecture

This is a **RAG (Retrieval-Augmented Generation) platform** for Azure Government, built as a FastAPI app with a four-stage pipeline:

1. **Ingestion** (`app/ingestion/`) — Downloads SOP documents (.md/.txt) from Azure Blob Storage, cleans and chunks them into `DocumentChunk` dataclasses.
2. **Indexing** (`app/indexing/`) — Generates embeddings via Azure OpenAI, stores vectors in both PostgreSQL/pgvector and Azure AI Search.
3. **Query** (`app/query/`) — Accepts a question, embeds it, performs hybrid search (keyword + vector) across both backends, then composes a grounded prompt for GPT-4.1.
4. **Safety** (`app/safety/`) — Pre-checks user input and post-checks model output against Azure AI Content Safety (Hate, Violence, SelfHarm, Sexual categories) with configurable severity thresholds.

The app exposes five endpoints: `/health`, `/ingest`, `/index`, `/query`, `/safety/check`.

### Dual-cloud strategy

One codebase targets both Azure Government (`AzureUSGovernment` / `usgovvirginia`) and Azure Commercial (`AzureCloud` / `eastus2`). Cloud selection is driven entirely by environment variables — there are no code branches for cloud type. The `Settings` class in `app/config.py` uses computed properties to derive the correct Azure endpoint suffixes.

### Infrastructure

Terraform modules under `infra/modules/` provision: OpenAI, PostgreSQL + pgvector, AI Search, Blob Storage, Content Safety, Managed Identity with RBAC. The root `infra/main.tf` composes them with a random suffix for globally-unique names.

## Conventions

### Python patterns

- All files begin with `from __future__ import annotations`.
- Full type annotations on all function signatures, including return types.
- Google-style docstrings with `Args:` / `Returns:` sections.
- `@dataclass` for structured data (`DocumentChunk`, `RAGResponse`, `SafetyResult`) — not ORM models.
- Module-level logger: `logger = logging.getLogger(__name__)`.
- Private helpers prefixed with underscore (e.g., `_get_openai_client()`).

### Module structure

Each app package (`ingestion`, `indexing`, `query`, `safety`) follows the same layout:
- One implementation file with a primary public function (e.g., `rag_query()`, `ingest_documents()`).
- Private `_get_*_client()` factory functions for Azure SDK clients.
- `__init__.py` with explicit `__all__` exports.

### Configuration

All settings are centralized in `app/config.py` via a `pydantic-settings` `Settings` class. Access the singleton as `from app.config import settings`. Never read `os.environ` directly in application code.

### Testing patterns

- `tests/conftest.py` provides shared fixtures: `mock_openai`, `mock_blob_service`, `mock_search_client`, `mock_content_safety`, `mock_postgres`, `test_client` (FastAPI), and sample data fixtures.
- An autouse `_test_env` fixture injects safe test environment variables — tests never call real Azure services.
- Unit tests use class-based organization (e.g., `TestDefaultConfigValues`).
- Integration tests are marked with `@pytest.mark.integration` and are excluded from default runs.

### Terraform

- Provider version: azurerm `~> 4.14`, Terraform `>= 1.5.0`.
- Variables use `azure_environment` (`"usgovernment"` or `"public"`) to select cloud endpoints.
- `project_prefix` must be lowercase with no special characters (used in resource naming).

<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read the current plan
<!-- SPECKIT END -->
