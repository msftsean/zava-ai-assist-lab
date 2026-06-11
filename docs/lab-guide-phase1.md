# 🏗️ Phase 1: Infrastructure Provisioning

> 📊 **Status:** ████████████████████ 100% Ready | 🏷️ **Version:** 1.0.0 | 📅 **Updated:** 2026-03-09

**⏱ Time Box: ~45 minutes**

## 🎯 Objective

Deploy the core Azure resources that make up the AI Assist platform. By the end of this phase, you will have a fully provisioned resource group containing Azure OpenAI, PostgreSQL with pgvector, Azure AI Search, Blob Storage, and Content Safety — all wired together with Managed Identity.

---

## ✅ Prerequisites

| Requirement | How to Verify |
|---|---|
| Azure CLI ≥ 2.50 | `az version` |
| Terraform ≥ 1.5 | `terraform version` |
| Subscription access (Contributor+) | `az account show` |
| `az login` completed | `az account list` shows your subscription |
| Git clone of this repo | You're reading this file |

---

## 📋 Step 1: Configure Environment (Gov vs. Commercial Dev Mode)

This lab supports **dual-mode deployment**. You'll use Commercial Azure for local development and testing, but the architecture is designed to deploy identically to Azure Government.

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your target cloud
# For this lab, use "commercial" unless you have a Gov subscription
export AZURE_CLOUD="commercial"   # or "usgovernment"
export AZURE_REGION="eastus2"     # or "usgovvirginia" for Gov
```

Set your Terraform variables:

```bash
cd infra

# Copy the tfvars template
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars
# Minimum required values:
#   project_name    = "aiassist"
#   environment     = "lab"
#   azure_region    = "eastus2"
#   cloud_mode      = "commercial"
```

> **🗣️ Facilitator Note:** Walk through the `.env` file together. Emphasize that the *only* difference between Gov and Commercial is the `AZURE_CLOUD` and `AZURE_REGION` values — the Terraform modules handle endpoint resolution internally. This is ADR-007 in action.

### ✔️ Verification

```bash
echo $AZURE_CLOUD   # Should print "commercial" or "usgovernment"
az account show --query "{name:name, cloud:environmentName}" -o table
```

---

## 📋 Step 2: Review Terraform Modules

Before deploying anything, take a few minutes to understand the module structure:

```
infra/
├── modules/
│   ├── ai_search/        # Azure AI Search (cognitive search)
│   ├── aks/              # AKS cluster (optional, not used in lab)
│   ├── content_safety/   # Azure Content Safety
│   ├── identity/         # Managed Identity + role assignments
│   ├── openai/           # Azure OpenAI with model deployments
│   ├── postgresql/       # PostgreSQL Flexible Server + pgvector
│   └── storage/          # Blob Storage for SOP documents
```

```bash
# List the modules
ls infra/modules/

# Glance at the main Terraform entry point
cat infra/main.tf
```

> **🗣️ Facilitator Note:** Call attention to the `identity/` module. It creates a single User-Assigned Managed Identity and grants it the minimum RBAC roles to each resource. This means zero secrets are stored anywhere — no connection strings, no API keys in config files.

### ✔️ Verification

Confirm you can read the module files and that `terraform init` succeeds:

```bash
cd infra
terraform init
```

Expected output: `Terraform has been successfully initialized!`

---

## 📋 Step 3: Deploy Resource Group

```bash
terraform plan -target=azurerm_resource_group.main
terraform apply -target=azurerm_resource_group.main -auto-approve
```

### ✔️ Verification

```bash
az group show --name "rg-aiassist-lab" --query "{name:name, location:location}" -o table
```

---

## 📋 Step 4: Deploy Azure OpenAI

```bash
terraform plan -target=module.openai
terraform apply -target=module.openai -auto-approve
```

This deploys:
- 🔹 An Azure OpenAI resource
- 🔹 A `gpt-4o` deployment (for chat completions)
- 🔹 A `text-embedding-ada-002` deployment (for embeddings)

> **🗣️ Facilitator Note:** In Azure Gov, Azure OpenAI is available in `usgovvirginia` and `usgovarizona`. Model availability may lag behind Commercial by a few weeks. Always check the [Azure Gov services-by-region page](https://azure.microsoft.com/en-us/explore/global-infrastructure/government/ai/).

### ✔️ Verification

```bash
az cognitiveservices account show \
  --name "oai-aiassist-lab" \
  --resource-group "rg-aiassist-lab" \
  --query "{name:name, kind:kind, provisioningState:properties.provisioningState}" \
  -o table
```

Expected: `provisioningState = Succeeded`

---

## 📋 Step 5: Deploy PostgreSQL Flexible Server with pgvector

```bash
terraform plan -target=module.postgresql
terraform apply -target=module.postgresql -auto-approve
```

This deploys:
- 🔹 PostgreSQL Flexible Server (version 16)
- 🔹 Enables the `vector` extension (pgvector)
- 🔹 Creates the `aiassist` database
- 🔹 Configures Entra ID (AAD) authentication

### ✔️ Verification

```bash
az postgres flexible-server show \
  --name "psql-aiassist-lab" \
  --resource-group "rg-aiassist-lab" \
  --query "{name:name, state:state, version:version}" \
  -o table
```

Verify pgvector is enabled:

```bash
az postgres flexible-server parameter show \
  --resource-group "rg-aiassist-lab" \
  --server-name "psql-aiassist-lab" \
  --name azure.extensions \
  --query "value" -o tsv
# Should include "vector" in the output
```

---

## 📋 Step 6: Deploy Azure AI Search

```bash
terraform plan -target=module.ai_search
terraform apply -target=module.ai_search -auto-approve
```

This deploys:
- 🔹 Azure AI Search service (Basic tier for lab)
- 🔹 Configures Managed Identity access

### ✔️ Verification

```bash
az search service show \
  --name "srch-aiassist-lab" \
  --resource-group "rg-aiassist-lab" \
  --query "{name:name, status:status, sku:sku.name}" \
  -o table
```

Expected: `status = running`

---

## 📋 Step 7: Deploy Storage Account

```bash
terraform plan -target=module.storage
terraform apply -target=module.storage -auto-approve
```

This deploys:
- 🔹 Storage Account with blob containers
- 🔹 A `sops` container for SOP documents
- 🔹 A `processed` container for chunked output

### ✔️ Verification

```bash
az storage account show \
  --name "staiassistlab" \
  --resource-group "rg-aiassist-lab" \
  --query "{name:name, provisioningState:provisioningState}" \
  -o table
```

---

## 📋 Step 8: Deploy Content Safety

```bash
terraform plan -target=module.content_safety
terraform apply -target=module.content_safety -auto-approve
```

This deploys:
- 🔹 Azure Content Safety resource
- 🔹 Configured for text analysis (hate, violence, self-harm, sexual categories)

### ✔️ Verification

```bash
az cognitiveservices account show \
  --name "cs-aiassist-lab" \
  --resource-group "rg-aiassist-lab" \
  --query "{name:name, kind:kind, provisioningState:properties.provisioningState}" \
  -o table
```

---

## 📋 Step 9: Deploy Identity & Role Assignments

```bash
terraform plan -target=module.identity
terraform apply -target=module.identity -auto-approve
```

This creates:
- 🔹 User-Assigned Managed Identity
- 🔹 RBAC role assignments connecting the identity to each service

### ✔️ Verification

```bash
az identity show \
  --name "id-aiassist-lab" \
  --resource-group "rg-aiassist-lab" \
  --query "{name:name, clientId:clientId}" \
  -o table
```

---

## ⚡ Full Deployment (Alternative)

If you prefer to deploy everything at once instead of step-by-step:

```bash
cd infra
terraform plan
terraform apply -auto-approve
```

### ✔️ Final Verification — All Resources

```bash
az resource list \
  --resource-group "rg-aiassist-lab" \
  --query "[].{Name:name, Type:type, State:provisioningState}" \
  -o table
```

You should see 6+ resources, all with `provisioningState = Succeeded`.

---

## 💡 Architecture Decision: Why pgvector AND AI Search?

These two search technologies serve **complementary roles**:

| Capability | pgvector | Azure AI Search |
|---|---|---|
| Vector similarity search | ✅ | ✅ |
| Full-text / keyword search | ❌ (basic `LIKE`) | ✅ (BM25, analyzers) |
| Hybrid search | ❌ | ✅ (vector + keyword) |
| Structured filtering (SQL) | ✅ (native SQL) | ⚠️ (OData filters) |
| Cost at scale | ✅ (cheap) | ⚠️ (dedicated compute) |
| Gov availability | ✅ | ✅ |
| Managed re-ranking | ❌ | ✅ (semantic ranker) |

**Bottom line:** We use AI Search for production-quality hybrid search with ranking, and pgvector as a cost-effective vector store that co-locates with application data. In many real deployments, you'll use both — AI Search for user-facing queries, pgvector for backend analytics and batch processing.

---

## 💡 Architecture Decision: Why Managed Identity?

Traditional approach:
```
App → reads API key from Key Vault → calls Azure OpenAI with key header
```

Our approach:
```
App → authenticates as Managed Identity → calls Azure OpenAI with AAD token
```

**Why this matters for Gov:**
- 🔹 **No secrets to rotate.** Managed Identity tokens are issued and rotated by the platform.
- 🔹 **No secrets to leak.** There are no connection strings in config files, environment variables, or CI/CD pipelines.
- 🔹 **Audit trail.** Every API call is tied to an identity in Entra ID, making compliance audits straightforward.
- 🔹 **FedRAMP alignment.** NIST 800-53 AC-2 (Account Management) and IA-2 (Identification and Authentication) are easier to satisfy when you eliminate shared secrets entirely.

---

## 🎉 Wrap-Up

At this point, your Azure environment is fully provisioned. You should have:

- [x] Resource group
- [x] Azure OpenAI with GPT-4o and embedding models
- [x] PostgreSQL Flexible Server with pgvector
- [x] Azure AI Search
- [x] Blob Storage with SOP containers
- [x] Content Safety
- [x] Managed Identity with RBAC roles

**Next:** [Phase 2 — SOP Ingestion and Indexing](lab-guide-phase2.md)

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — full lab guide |
