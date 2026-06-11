# MSI AI Assist Lab - Customer Runbook

A self-service guide to deploy and run the AI Assist Lab in your own Azure subscription. The lab is a Retrieval-Augmented Generation (RAG) platform with a layered AI safety pipeline (Prompt Shields, Content Safety on input and output) in front of Azure OpenAI. It runs unchanged on Azure Commercial or Azure Government; the cloud is selected entirely by configuration.

Estimated time: about 1.5 to 2 hours (most of it Azure provisioning).

## 1. What you will build

A FastAPI service with a four-stage pipeline:

1. Ingestion - load SOP documents (.md / .txt) from Blob Storage, clean and chunk them.
2. Indexing - generate embeddings with Azure OpenAI, store vectors in PostgreSQL/pgvector and Azure AI Search.
3. Query - embed a question, run hybrid search, compose a grounded prompt for the chat model.
4. Safety - check user input and model output against Azure AI Content Safety with configurable thresholds.

Endpoints: `/health`, `/ingest`, `/index`, `/query`, `/safety/check`, plus an interactive guardrails console at `/demo/`.

## 2. Prerequisites

- An Azure subscription where you can create resources (Commercial or Government).
- Quota for Azure OpenAI in your target region (a chat model such as gpt-4o and an embedding model such as text-embedding-3-small).
- Tools on your workstation:
  - Azure CLI (`az`)
  - Terraform >= 1.5.0
  - Python 3.12
  - Docker (optional, for the local PostgreSQL + pgvector container)
- Sign in: `az login` (for Government, `az cloud set --name AzureUSGovernment` first, then `az login`).

## 3. Provision Azure resources (Terraform)

The Terraform under `infra/` provisions: Azure OpenAI, PostgreSQL Flexible Server with pgvector, Azure AI Search, Blob Storage, Content Safety, and a Managed Identity with the required RBAC.

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your own values:

- `azure_environment` - `"public"` for Commercial or `"usgovernment"` for Government.
- `location` - for example `eastus2` (Commercial) or `usgovvirginia` (Government).
- `project_prefix` - lowercase letters/numbers only (used in resource names).
- `resource_group_name` - your resource group.
- `openai_model_name` / `openai_model_version` - the chat model you have quota for.
- `postgres_admin_username` / `postgres_admin_password` - set a strong password. Do not commit this file.

Then:

```bash
terraform init
terraform plan -out tfplan
terraform apply tfplan
```

Note the outputs (endpoints and resource names) for the next step. `terraform.tfvars` and `*.tfstate` are gitignored; keep them private.

## 4. Configure the application

```bash
cd ../app
cp .env.example .env
```

Fill in `.env` from your Terraform outputs. Key settings:

- `AZURE_CLOUD` - `AzureCloud` or `AzureUSGovernment`.
- `AZURE_LOCATION` - your region.
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION`.
- `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME`.
- `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_STORAGE_CONTAINER`.
- `AZURE_CONTENT_SAFETY_ENDPOINT`.
- PostgreSQL host/port/db/user/password.

### Authentication: keyless first (recommended)

Leave the `*_API_KEY` values empty. With keys blank, the app authenticates via `DefaultAzureCredential` (your `az login` identity, or a Managed Identity when hosted). Grant your identity these roles on the resources:

- Cognitive Services OpenAI User (on the Azure OpenAI resource)
- Cognitive Services User (on the Content Safety resource)
- Search Index Data Contributor (on the AI Search resource)
- Storage Blob Data Contributor (on the Storage account)

API keys are supported as a fallback (set the `*_API_KEY` values), but keyless Entra ID auth is the default and is required when a resource has local auth disabled. Never commit `.env` or any key.

## 5. Install and run

```bash
# from repo root
pip install -r app/requirements.txt

# optional: local PostgreSQL + pgvector
docker compose up -d

uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/health` to confirm the service is up, and `http://localhost:8000/demo/` for the guardrails console.

## 6. Verify end to end

1. Health: `curl http://localhost:8000/health` returns OK.
2. Ingest sample SOPs (the repo ships sample SOPs under `evals/datasets/sample_sops/` and `docs/sops/`): call `/ingest` then `/index`.
3. Grounded query - ask a question answerable from the SOPs:

   ```bash
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"question": "What are the password requirements for system access?"}'
   ```

   Expect a grounded answer with source citations.

4. Guardrails block - confirm the safety pipeline blocks an attack. In the `/demo/` console, run the "Prompt injection" and an "Explicit violent how-to" scenario and observe the verdicts (`injection_flagged`, `blocked_input`). A blocked request never reaches or never returns from the model.

## 7. Run the tests and offline eval

No live Azure services are needed for these.

```bash
pip install pytest pyyaml        # not in app/requirements.txt
pytest                            # unit tests (integration excluded by default)
pytest -m integration             # integration tests (mocked Azure)

# Eval harness in mock mode (set UTF-8 on Windows: PYTHONUTF8=1)
python -m evals.harness.eval_runner --mock
```

## 8. Safety tuning

The safety pipeline supports `strict`, `standard`, and `relaxed` filter profiles and per-category thresholds (Hate, Violence, SelfHarm, Sexual). You can edit thresholds, add blocklist terms, and toggle Prompt Shields at runtime from the `/demo/` console without restarting. Prompt Shields region availability differs from base Content Safety; verify your region supports it (most Commercial regions do; confirm for Government).

## 9. Cloud selection (Commercial vs Government)

There are no code branches for cloud type. Set `azure_environment` in Terraform and `AZURE_CLOUD` / `AZURE_LOCATION` in `.env`; the app derives the correct endpoint suffixes automatically. The same codebase runs in both clouds.

## 10. Troubleshooting

- 401/403 from Content Safety or OpenAI: your identity is missing the RBAC role above, or a stale `az login`. Re-run `az login` and confirm the role assignment.
- Prompt Shields returns 401/403: `AZURE_CONTENT_SAFETY_*` not set, or Managed Identity lacks Cognitive Services User.
- DNS or connection errors to Azure endpoints: confirm `az` and `curl` can reach the endpoint; some networks require a proxy.
- Empty search results: confirm `/ingest` and `/index` ran and the index name matches `AZURE_SEARCH_INDEX_NAME`.
- On Windows, set `PYTHONUTF8=1` before the eval harness to avoid encoding errors.

## 11. Security notes

- Secrets live only in `.env` and `terraform.tfvars`, both gitignored. Never commit them.
- Prefer keyless Entra ID auth with least-privilege RBAC over API keys.
- The guardrails pipeline is defense in depth: Prompt Shields and an offline injection-regex fallback, Content Safety on input and output, and a configurable blocklist. Every request produces a structured audit entry suitable for an audit pipeline.
