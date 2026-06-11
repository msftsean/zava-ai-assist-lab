# 🏛️ Architecture Decision Records (ADRs)

> 📊 **Status:** ████████████████████ 100% Complete | 🏷️ **Version:** 1.1.0 | 📅 **Updated:** 2026-03-10

This document captures the key architectural decisions made for the AI Assist platform, along with their context, rationale, and consequences.

---

## 🤖 ADR-001: Use Azure OpenAI Over Direct OpenAI API

**Status:** ✅ Accepted
**Date:** 2024-01-10

### 🔍 Context

We need a large language model (LLM) and embedding model for the AI Assist platform. The two primary options are:
1. **OpenAI API** (direct, via `api.openai.com`)
2. **Azure OpenAI Service** (Microsoft-hosted, via `*.openai.azure.com`)

Both provide access to the same underlying models (GPT-4o, text-embedding-ada-002, etc.).

### ✅ Decision

Use **Azure OpenAI Service** exclusively.

### 💡 Rationale

- **FedRAMP authorization:** Azure OpenAI is available in Azure Government regions (`usgovvirginia`, `usgovarizona`) and inherits Azure's FedRAMP High authorization. The direct OpenAI API has no FedRAMP authorization.
- **Data residency:** Azure OpenAI processes data within the Azure region you deploy to. Direct OpenAI API routes data through OpenAI's infrastructure with no region guarantees.
- **Network isolation:** Azure OpenAI supports Private Endpoints, VNet integration, and IP restrictions. Direct OpenAI API does not.
- **Identity integration:** Azure OpenAI authenticates via Entra ID (AAD), enabling Managed Identity auth with zero secrets. Direct OpenAI API uses static API keys.
- **Compliance logging:** Azure OpenAI integrates with Azure Monitor and diagnostic logging, required for continuous monitoring in FedRAMP.

### ⚖️ Consequences

- Model availability in Azure Gov may lag behind the direct OpenAI API by weeks or months.
- Pricing may differ slightly between Azure OpenAI and direct OpenAI API.
- The application code uses Azure OpenAI SDK (`openai` library with `azure` configuration), not the generic OpenAI SDK.

---

## 🗄️ ADR-002: pgvector + AI Search Dual Strategy

**Status:** ✅ Accepted
**Date:** 2024-01-10

### 🔍 Context

The platform needs vector search for semantic retrieval. The two leading options in Azure are:
1. **pgvector** — PostgreSQL extension for vector similarity search
2. **Azure AI Search** — Managed search service with vector, keyword, and hybrid capabilities

### ✅ Decision

Use **both** pgvector and Azure AI Search, each for its strengths.

### 💡 Rationale

| Capability | pgvector | Azure AI Search |
|---|---|---|
| Pure vector search | ✅ | ✅ |
| Hybrid search (vector + keyword) | ❌ | ✅ |
| SQL-based filtering and joins | ✅ | ❌ |
| Cost efficiency at scale | ✅ (shared DB) | ⚠️ (dedicated compute) |
| Managed re-ranking (semantic ranker) | ❌ | ✅ |
| Azure Gov availability | ✅ | ✅ |

- **AI Search** is the primary retrieval backend for user-facing queries, providing hybrid search (vector + BM25) with semantic re-ranking for the best possible retrieval quality.
- **pgvector** is used for backend tasks: batch analytics, programmatic queries that benefit from SQL joins, and as a cost-effective secondary store.

### ⚖️ Consequences

- Two stores to maintain and keep in sync during ingestion.
- The ingestion pipeline must write to both stores.
- Operators need familiarity with both PostgreSQL and Azure AI Search administration.
- If budget is constrained, pgvector alone is a viable starting point — but hybrid search quality will be lower.

---

## 🛡️ ADR-003: Content Safety as Mandatory Guardrail

**Status:** ✅ Accepted
**Date:** 2024-01-10

### 🔍 Context

The platform generates text responses based on user queries. In a government context, we must ensure that neither user input nor model output contains harmful content (hate speech, violence, self-harm, sexually explicit content).

Options:
1. Rely on Azure OpenAI's built-in content filtering
2. Use Azure Content Safety as a standalone service
3. Use both

### ✅ Decision

Use **Azure Content Safety as a mandatory, standalone guardrail** in addition to Azure OpenAI's built-in filters. Content Safety checks are enforced at the application layer (pre-check on input, post-check on output) and cannot be bypassed.

### 💡 Rationale

- **Independent control:** Azure OpenAI's built-in filters are opaque — you can't fully customize thresholds or get detailed severity scores. Content Safety provides granular control with numeric severity levels (0–6) for each harm category.
- **Audit trail:** Content Safety results are logged independently, creating a clear audit trail for compliance. Azure OpenAI's built-in filtering does not provide detailed logs.
- **Pre-check saves cost:** By checking user input *before* calling the LLM, we avoid spending tokens on harmful queries. Azure OpenAI's filters only apply *after* the model processes the input.
- **Defense in depth:** Using both Content Safety and OpenAI's built-in filters provides two independent safety layers. If one misses something, the other catches it.
- **Gov requirement:** For FedRAMP, demonstrating explicit safety controls (not just "the AI handles it") is expected in the System Security Plan.

### ⚖️ Consequences

- Adds ~100ms latency per request (two Content Safety API calls: pre and post).
- Adds cost (~$1 per 1,000 text records analyzed).
- Requires threshold calibration — too strict causes false positives, too lenient allows harmful content.
- Must be included in the authorization boundary for FedRAMP.

---

## 🔐 ADR-004: Managed Identity for Service Authentication

**Status:** ✅ Accepted
**Date:** 2024-01-10

### 🔍 Context

The application needs to authenticate to multiple Azure services: OpenAI, PostgreSQL, AI Search, Storage, Content Safety. Traditional approaches use connection strings, API keys, or service principal secrets.

### ✅ Decision

Use **User-Assigned Managed Identity** for all service-to-service authentication. No API keys, connection strings, or secrets are stored in code, configuration files, or environment variables.

### 💡 Rationale

- **Zero secret management:** Managed Identity tokens are issued and rotated by the Azure platform. There are no secrets to store, rotate, or accidentally expose.
- **NIST 800-53 alignment:**
  - AC-2 (Account Management): Managed Identities are centrally managed in Entra ID.
  - IA-2 (Identification and Authentication): Every API call is authenticated with a short-lived token tied to a specific identity.
  - IA-5 (Authenticator Management): No static credentials to manage.
- **Reduced attack surface:** No API keys in source code, CI/CD pipelines, or environment variables. A leaked `.env` file or misconfigured pipeline cannot expose service credentials.
- **Audit trail:** Every API call is tied to the Managed Identity's object ID in Entra ID, making it trivial to trace access in logs.

### ⚖️ Consequences

- Local development is slightly more complex — developers must use `az login` or the `DefaultAzureCredential` chain.
- RBAC role assignments must be managed carefully — the identity needs the minimum required roles on each resource.
- Some Azure services require specific RBAC roles for Managed Identity auth (e.g., `Cognitive Services OpenAI User` for Azure OpenAI).

---

## 📦 ADR-005: Terraform Over ARM Templates

**Status:** ✅ Accepted
**Date:** 2024-01-10

### 🔍 Context

We need Infrastructure as Code (IaC) to deploy Azure resources reproducibly. The main options are:
1. **ARM Templates** — Azure-native, JSON-based
2. **Bicep** — Azure-native, DSL that compiles to ARM
3. **Terraform** — Multi-cloud, HCL-based, uses the AzureRM provider

### ✅ Decision

Use **Terraform** with the AzureRM provider.

### 💡 Rationale

- **Readability:** HCL is more readable than ARM JSON. Engineers unfamiliar with the IaC can understand the Terraform files.
- **Module system:** Terraform modules provide clean separation of concerns. Each Azure service gets its own module (`modules/openai/`, `modules/postgresql/`, etc.).
- **State management:** Terraform state tracks deployed resources and enables `plan` (dry-run) before `apply`. ARM templates deploy imperatively with no built-in diff.
- **Multi-cloud portability:** While this project targets Azure, Terraform knowledge transfers to AWS/GCP. ARM/Bicep skills are Azure-only.
- **Team familiarity:** The team has existing Terraform expertise.
- **Gov compatibility:** The AzureRM Terraform provider supports Azure Government by setting the `environment` argument to `usgovernment`.

### ⚖️ Consequences

- Terraform state must be stored securely (Azure Storage backend with encryption).
- AzureRM provider updates may lag behind ARM API changes.
- Bicep is a valid alternative — if the team prefers it, the modules can be rewritten in Bicep with minimal architectural impact.

---

## 🐍 ADR-006: Python for Application Layer

**Status:** ✅ Accepted
**Date:** 2024-01-10

### 🔍 Context

The application layer (ingestion pipeline, indexing, query engine, safety checks) needs a programming language. Candidates:
1. **Python** — dominant in AI/ML ecosystem
2. **C# / .NET** — strong Azure SDK support
3. **TypeScript/Node.js** — strong for web APIs

### ✅ Decision

Use **Python** for all application layer code.

### 💡 Rationale

- **AI/ML ecosystem:** Python has the richest ecosystem for AI/ML workloads: `openai`, `langchain`, `llama-index`, `tiktoken`, `numpy`, `psycopg2`, and the Azure SDKs all have first-class Python support.
- **Azure SDK quality:** The Azure SDK for Python (`azure-identity`, `azure-search-documents`, `azure-ai-contentsafety`) is well-maintained and supports all features needed for this project.
- **Rapid prototyping:** Python enables fast iteration during the lab — less boilerplate, easier debugging, REPL for exploration.
- **Team skills:** The team has strong Python experience.
- **pgvector support:** `psycopg2` with `pgvector` extension support makes PostgreSQL vector operations straightforward.

### ⚖️ Consequences

- Python's runtime performance is lower than C#/Go — acceptable for this workload since latency is dominated by API calls, not local compute.
- Type safety relies on conventions and optional type hints (mypy) rather than compile-time checks.
- Deployment to Azure (Functions, Container Apps, AKS) works well with Python, but cold start times can be higher than compiled languages.

---

## 🌐 ADR-007: Dual-Mode Deployment (Gov Design, Commercial Dev)

**Status:** ✅ Accepted
**Date:** 2024-01-10

### 🔍 Context

The platform is designed for Azure Government but needs a practical development workflow. Azure Gov subscriptions are limited, expensive, and may have access restrictions that slow down development.

### ✅ Decision

Implement a **dual-mode architecture** where:
- **Design target:** Azure Government (FedRAMP High, Gov-specific endpoints)
- **Development environment:** Azure Commercial (freely accessible, same services)
- **Mode switch:** A single configuration value (`cloud_mode = "commercial" | "usgovernment"`) controls endpoint resolution, region selection, and any Gov-specific behavior.

### 💡 Rationale

- **Developer productivity:** Engineers can develop and test without needing Azure Gov credentials or waiting for Gov-specific provisioning.
- **Cost efficiency:** Commercial Azure is generally cheaper and has more flexible pay-as-you-go options for development.
- **Architectural fidelity:** The application code is *identical* in both modes. Only infrastructure configuration (endpoints, regions) changes. This means code tested in Commercial mode will work in Gov mode without code changes.
- **Lab practicality:** For this hands-on lab, most participants won't have Azure Gov access. Commercial mode lets everyone participate.

### ⚖️ Consequences

- Must maintain a mapping of Commercial ↔ Gov service endpoints.
- Some features available in Commercial may not be available in Gov (e.g., newer model versions) — the Gov Compatibility Checklist tracks these differences.
- Testing in Gov is still required before production deployment — Commercial testing does not replace Gov testing.
- The `cloud_mode` configuration must be validated in CI to prevent accidental deployment of Commercial config to Gov.

### 🛠️ Implementation

```python
# app/utils/cloud_config.py

CLOUD_ENDPOINTS = {
    "commercial": {
        "openai_suffix": "openai.azure.com",
        "search_suffix": "search.windows.net",
        "storage_suffix": "blob.core.windows.net",
        "auth_authority": "https://login.microsoftonline.com",
    },
    "usgovernment": {
        "openai_suffix": "openai.azure.us",
        "search_suffix": "search.azure.us",
        "storage_suffix": "blob.core.usgovcloudapi.net",
        "auth_authority": "https://login.microsoftonline.us",
    },
}
```

```hcl
# infra/variables.tf

variable "cloud_mode" {
  type        = string
  default     = "commercial"
  description = "Target cloud: 'commercial' or 'usgovernment'"
  validation {
    condition     = contains(["commercial", "usgovernment"], var.cloud_mode)
    error_message = "cloud_mode must be 'commercial' or 'usgovernment'."
  }
}
```

---

## 🛡️ ADR-008: App-Layer Filter Profiles Above Azure Content Safety

**Status:** ✅ Accepted
**Date:** 2026-03-10

### 🔍 Context

Azure Content Safety analyzes text and returns severity scores (0–6) across four harm categories. The service applies a single set of thresholds at the API level. However, different deployment contexts require different sensitivity levels:

- **Government/FedRAMP** deployments need the strictest thresholds (block at severity ≥ 1)
- **Enterprise internal** tools need moderate thresholds (block at severity ≥ 2)
- **Developer/QA environments** need relaxed thresholds to test with boundary content (block at severity ≥ 4)
- **Multi-tenant SaaS** needs per-tenant customizable thresholds

Azure Content Safety's platform-level filters cannot be customized per-application or per-tenant from a single resource. Changing thresholds requires API-level reconfiguration, not a simple code change.

### ✅ Decision

Implement **application-layer filter profiles** that process Content Safety API scores against configurable, per-context thresholds. Provide three built-in profiles (`strict`, `standard`, `relaxed`) and support custom profiles with per-category thresholds.

### 💡 Rationale

- **Separation of concerns:** Azure Content Safety handles the analysis (severity scoring). The application handles the policy decision (what to block).
- **Multi-tenant flexibility:** Different profiles can be applied per user, per tenant, or per deployment without changing Azure configuration.
- **Environment parity:** The same Content Safety resource can serve dev, staging, and production — only the filter profile changes.
- **Testability:** `evaluate_all_profiles()` shows how all profiles would handle the same content, making it easy to calibrate thresholds.
- **Gov compliance:** The `strict` profile enforces the most conservative thresholds required for FedRAMP, while `standard` and `relaxed` serve less regulated contexts.

### ⚖️ Consequences

- Two layers of threshold logic (Azure-level and app-level) require clear documentation to avoid confusion.
- Profile selection must be tied to the deployment context (e.g., environment variable or tenant configuration).
- Custom profiles must be validated to ensure they don't inadvertently weaken safety below organizational minimums.

### 🛠️ Implementation

```python
# app/safety/filter_profiles.py

PROFILES = {
    "strict":   {"hate": 1, "violence": 1, "self_harm": 1, "sexual": 1},
    "standard": {"hate": 2, "violence": 2, "self_harm": 2, "sexual": 2},
    "relaxed":  {"hate": 4, "violence": 4, "self_harm": 4, "sexual": 4},
}

# Key functions:
# get_profile(name) → dict of thresholds
# apply_profile(name, scores) → FilterResult (blocked, reason, details)
# evaluate_all_profiles(scores) → dict of profile_name → FilterResult
# register_profile(name, thresholds) → registers a custom profile
```

---

## 🔒 ADR-009: Pattern-Based Prompt Injection Detection

**Status:** ✅ Accepted (interim solution)
**Date:** 2026-03-10

### 🔍 Context

During content safety testing, we discovered a critical gap: **Azure Content Safety does NOT detect prompt injection attacks.** All three injection test cases (instruction override, role manipulation, system prompt extraction) scored severity 0/0/0/0 across all four harm categories.

This is by design — Content Safety analyzes content **toxicity** (hate speech, violence, etc.), not prompt injection **intent**. A prompt injection like "Ignore all previous instructions" contains no toxic content, so Content Safety correctly scores it as safe.

Azure offers **Azure AI Prompt Shields** (preview) for injection detection, but it is not yet generally available and cannot be relied upon for production Gov deployments.

### ✅ Decision

Implement a **pattern-based prompt injection detector** at the application layer using regex patterns with weighted confidence scoring. This serves as an interim defense until Azure AI Prompt Shields reaches GA.

### 💡 Rationale

- **Defense-in-depth:** Without injection detection, the safety layer has a known, exploitable gap. Even imperfect pattern matching is better than no detection.
- **Known patterns:** The most common injection techniques (role manipulation, instruction override, delimiter injection, system prompt extraction) follow recognizable patterns that regex can catch.
- **Weighted scoring:** Not all pattern matches are equally concerning. Weighted confidence scoring (none/low/medium/high) reduces false positives while catching high-confidence attacks.
- **Immediate availability:** Unlike Azure AI Prompt Shields (preview), this runs entirely at the application layer with no external dependencies.
- **Replaceable:** The module is designed to be replaced or augmented with Azure AI Prompt Shields when it reaches GA.

### ⚖️ Consequences

- Pattern-based detection can be evaded by novel or obfuscated injection techniques. It catches known patterns, not unknown ones.
- Regex patterns must be maintained and updated as new injection techniques emerge.
- False positives are possible — legitimate queries that happen to match patterns (e.g., a user asking "how do I override system settings?") may be flagged.
- This is explicitly an **interim solution** — the long-term approach should use Azure AI Prompt Shields or equivalent ML-based detection.

### 🛠️ Implementation

```python
# app/safety/prompt_shield.py

# 12 regex patterns across categories:
# - Instruction override ("ignore previous instructions", "disregard above")
# - Role manipulation ("you are now", "act as", "pretend to be")
# - System prompt extraction ("repeat your system prompt", "show me your instructions")
# - Delimiter injection ("###", "---", "```", "[SYSTEM]")
# - ... and 8 more categories

# Key function:
# scan_for_injection(text) → ShieldResult
#   - is_injection: bool
#   - confidence: "none" | "low" | "medium" | "high"
#   - matched_patterns: list[str]
#   - details: str
```

> **📝 Note:** When Azure AI Prompt Shields reaches GA, integrate it as the primary detection layer and retain this pattern-based approach as a fallback. Update this ADR at that time.

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — 7 ADRs covering AI, search, safety, identity, IaC, language, and deployment |
| 1.1.0 | 2026-03-10 | Squad (Beacon 🔦) | Added ADR-008 (app-layer filter profiles) and ADR-009 (pattern-based prompt injection detection) |
