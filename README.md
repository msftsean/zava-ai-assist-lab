# MSI Hands-on Lab: Azure Gov AI Assist Architecture & Deployment

> **Move from architecture decisions to practical execution.** Leave with a repeatable deployment pattern, starter IaC, shared understanding of eval/safety/RAG, and documented next steps.

[![Lab Status](https://img.shields.io/badge/status-hands--on%20lab-blue)](#)
[![Cloud Target](https://img.shields.io/badge/cloud-Azure%20Government-orange)](#)
[![Dev Mode](https://img.shields.io/badge/dev%20mode-Azure%20Commercial-green)](#)

---

## 🎯 What You'll Build

A complete AI-assisted operations platform using RAG (Retrieval-Augmented Generation) on Azure Government — with customizable content filters, prompt injection detection, and a hands-on safety lab:

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│  SOP Docs   │───▶│  Blob Store  │───▶│  Ingestion +    │───▶│  AI Search   │
│  (.md/.txt) │    │              │    │  Chunking       │    │  (vectors)   │
└─────────────┘    └──────────────┘    └────────┬────────┘    └──────┬───────┘
                                                │                    │
                                                ▼                    │
                                       ┌────────────────┐           │
                                       │  PostgreSQL    │           │
                                       │  + pgvector    │           │
                                       └────────┬───────┘           │
                                                │                    │
                   ┌────────────────┐           ▼                    ▼
                   │ Content Safety │◀── ┌────────────────────────────────┐
                   │ (pre + post)   │──▶ │     RAG Query Engine           │
                   └────────────────┘    │  retrieve → compose → generate │
                                         └───────────────┬────────────────┘
                                                         │
                                                         ▼
                                                  ┌─────────────┐
                                                  │ Azure OpenAI│
                                                  │  (GPT-4o)   │
                                                  └─────────────┘
```

## 📋 Target Stack

| Component | Azure Service | Purpose |
|-----------|--------------|---------|
| LLM | Azure OpenAI (GPT-4o) | Generation, embeddings |
| Vector DB | PostgreSQL Flexible Server + pgvector | Vector storage & similarity search |
| Search | Azure AI Search | Hybrid search (vector + keyword) |
| Safety | Azure AI Content Safety | Input/output guardrails |
| Storage | Azure Blob Storage | SOP document ingestion |
| Compute | AKS (CPS-managed pattern) | Application hosting |
| IaC | Terraform + AZD | Infrastructure provisioning |
| Identity | Managed Identity | Zero-secret service auth |

## 🌐 Cloud & Region Strategy

This lab uses a **dual-mode deployment** strategy:

| Mode | Cloud | Region | Use Case |
|------|-------|--------|----------|
| **Gov (default)** | `AzureUSGovernment` | `usgovvirginia` | Production target |
| **Commercial Dev** | `AzureCloud` | `eastus2` | Lab development & testing |

**One codebase, zero code forks.** Switch modes via environment variables:

```bash
# Gov mode (default)
export AZURE_CLOUD=AzureUSGovernment
export AZURE_LOCATION=usgovvirginia

# Commercial dev mode
export AZURE_CLOUD=AzureCloud
export AZURE_LOCATION=eastus2
```

## 🗂️ Repository Structure

```
ai_assist_lab/
├── .squad/                    # Squad agent team (X-Men-inspired personas)
│   └── agents/                # Synapse, Tempest, Forge, Mend, Beacon
├── infra/                     # Terraform infrastructure-as-code
│   ├── modules/               # Modular resources
│   │   ├── openai/            # Azure OpenAI
│   │   ├── postgresql/        # PostgreSQL + pgvector
│   │   ├── ai_search/         # Azure AI Search
│   │   ├── storage/           # Blob Storage
│   │   ├── content_safety/    # Content Safety
│   │   ├── identity/          # Managed Identity + RBAC
│   │   └── aks/               # AKS stub
│   └── azd/                   # Azure Developer CLI config
├── app/                       # Python RAG application
│   ├── ingestion/             # SOP document ingestion
│   ├── indexing/              # Embedding + indexing
│   ├── query/                 # RAG query engine
│   ├── safety/                # Content safety filters
│   │   ├── filter_profiles.py # Customizable filter profiles (strict/standard/relaxed/custom)
│   │   └── prompt_shield.py   # Prompt injection detection (12 patterns, confidence scoring)
│   └── utils/                 # Text processing utilities
├── tests/                     # Automated tests
│   ├── unit/                  # Unit tests (no Azure needed)
│   └── integration/           # Integration tests (mocked)
├── evals/                     # Evaluation harness
│   ├── datasets/              # Golden questions + sample SOPs
│   └── harness/               # Eval runner + reporting
├── docs/                      # Lab guides & documentation
├── scripts/                   # Deployment & setup scripts
│   ├── demo_content_safety.py # Content safety demo script
│   └── lab_content_safety.py  # Interactive 5-exercise content safety lab
├── Dockerfile                 # Container image
├── docker-compose.yml         # Local dev environment
└── mkdocs.yml                 # MkDocs config (optional)
```

## 🚀 Quick Start

> New here? Follow the end-to-end [Customer Runbook](docs/CUSTOMER-RUNBOOK.md) to provision, configure, run, and verify the lab in your own Azure subscription.

### Prerequisites

- Azure CLI (`az`) — authenticated
- Terraform ≥ 1.5
- Python ≥ 3.11
- Docker (optional, for local dev)
- Git

### 1. Clone & Configure

```bash
git clone <repo-url> && cd ai_assist_lab
cp app/.env.example app/.env
# Edit app/.env with your Azure resource values
```

### 2. Deploy Infrastructure

```bash
# Commercial dev mode
source scripts/setup-env.sh
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars
terraform init && terraform plan && terraform apply
```

### 3. Run the Application

```bash
pip install -r app/requirements.txt
uvicorn app.main:app --reload --port 8000
```

Or with Docker:

```bash
docker compose up -d
```

### 4. Run Tests

```bash
# Unit tests (no Azure services needed)
pytest

# Integration tests
pytest -m integration

# Evaluation harness
python -m evals.harness.eval_runner --mock
```

### 5. Open the Guardrails Console

With the app running, open the interactive guardrails console:

```bash
http://localhost:8000/demo/
```

## 🛡️ Guardrails Demo

An interactive browser demo that runs a layered safety pipeline in front of Azure OpenAI: **Prompt Shields → Input Content Safety → Azure OpenAI → Output Content Safety**, with a live audit trail. Built to support Motorola Solutions / FedRAMP-style architecture conversations — switch between `strict`/`standard`/`relaxed` profiles, edit thresholds, add blocklist terms, and toggle Prompt Shields without a restart.

Quick start:

```bash
cp app/.env.example app/.env   # set AZURE_OPENAI_* and AZURE_CONTENT_SAFETY_*
pip install -r app/requirements.txt
uvicorn app.main:app --reload --port 8000
# open http://localhost:8000/demo/
```

Full walkthrough, endpoint reference, and presenter script: [docs/demo-guardrails.md](docs/demo-guardrails.md).

## 📚 Lab Phases

| Phase | Title | Time | Guide |
|-------|-------|------|-------|
| 1 | Infrastructure Provisioning | ~45 min | [docs/lab-guide-phase1.md](docs/lab-guide-phase1.md) |
| 2 | SOP Ingestion & Indexing | ~30 min | [docs/lab-guide-phase2.md](docs/lab-guide-phase2.md) |
| 3 | RAG Query Flow | ~30 min | [docs/lab-guide-phase3.md](docs/lab-guide-phase3.md) |
| 4 | Safety Integration | ~20 min | [docs/lab-guide-phase4.md](docs/lab-guide-phase4.md) |
| 5 | Testing & Evaluation | ~25 min | [docs/lab-guide-phase5.md](docs/lab-guide-phase5.md) |
| 6 | Content Safety Lab (Hands-on) | ~30 min | [scripts/lab_content_safety.py](scripts/lab_content_safety.py) |

**Total session time: ~4.5 hours** (includes ~3 hours hands-on + breaks and discussion)

## 🤖 Squad Team

This repo is orchestrated by [Squad](https://github.com/bradygaster/squad) with X-Men-inspired agent personas:

| Codename | Role | Specialty |
|----------|------|-----------|
| **Synapse** 🧠 | Lead / Architect | Telepathic strategist — sees connections, coordinates the team |
| **Tempest** ⛈️ | Cloud / Reliability | Controls the storms of cloud infra — DR, Gov compliance |
| **Forge** 🔧 | IaC / DevOps | Tech-savant — builds fast, iterates faster |
| **Mend** 💚 | Test / Quality | Healer — fixes broken code through relentless testing |
| **Beacon** 🔦 | Docs / Dashboard | Scout — lights the path for others to follow |

## 📖 Key Documents

- [Architecture Decisions](docs/architecture-decisions.md) — Why we chose what we chose
- [Gov Compatibility Checklist](docs/gov-compatibility-checklist.md) — What to verify in a real Gov subscription
- [Facilitator Guide](docs/facilitator-guide.md) — For lab leaders
- [Troubleshooting](docs/troubleshooting.md) — When things go sideways
- [Non-Goals](docs/non-goals.md) — What this lab deliberately does NOT cover
- [Evaluation Guide](evals/README.md) — Running and extending the eval harness

## ⚠️ Non-Goals

This lab is intentionally scoped. It is **NOT**:

- A production-ready deployment
- A security hardening guide
- A cost optimization exercise
- A multi-region HA setup
- A CI/CD pipeline implementation

See [docs/non-goals.md](docs/non-goals.md) for details.

## 🏛️ Lab Outcomes

Participants leave with:

1. ✅ A **repeatable Azure Gov deployment pattern** (Terraform + AZD)
2. ✅ **Starter infrastructure-as-code** (real, not slides)
3. ✅ A clear understanding of **RAG architecture, model evaluation, and safety enforcement**
4. ✅ Documented **next steps toward March FedRAMP Stage**

## 📊 Latest Test Results

| Test Suite | Count | Status | Duration |
|-----------|-------|--------|----------|
| Unit Tests | 49 | ✅ All Passed | 5.07s |
| Integration Tests | 19 | ✅ All Passed | 3.08s |
| Golden Questions (Mock) | 10 | ✅ All Passed | — |
| Golden Questions (Live) | 10 | ✅ All Passed | 3.06s avg |
| **Total** | **88** | **✅ 100% Pass Rate** | — |

## 📋 Version History

| Version | Date | Status | Changes |
|---------|------|--------|---------|
| 1.1.0 | 2026-03-09 | 🟢 Current | Phase 6 Content Safety Lab, filter profiles, prompt shield, 88/88 tests |
| 1.0.0 | 2026-03-09 | 🔵 Previous | Initial release — complete lab with IaC, app, tests, evals, dashboard |
| 0.1.0 | 2026-03-09 | 🔴 Superseded | Repository scaffolding |

## 📄 License

Internal use — MSI Hands-on Lab.

---

*Built with [Squad](https://github.com/bradygaster/squad) 🤖*