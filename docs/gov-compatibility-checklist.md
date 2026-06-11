# 🏛️ Azure Government Compatibility Checklist

> 📊 **Status:** ██████████░░░░░░░░░░ 50% — Requires Gov Subscription Validation | 🏷️ **Version:** 1.0.0 | 📅 **Updated:** 2026-03-09

This checklist tracks the differences between Azure Commercial and Azure Government that affect the AI Assist platform. Use it to verify Gov readiness before deploying to a real Azure Government subscription.

---

## 🇺🇸 Service Availability in Azure Gov

| Service | Commercial | Azure Gov | Gov Regions | Notes |
|---|---|---|---|---|
| Azure OpenAI | ✅ | ✅ | usgovvirginia, usgovarizona | Model availability may differ |
| PostgreSQL Flexible Server | ✅ | ✅ | usgovvirginia, usgovarizona, usgovtexas | pgvector extension supported |
| Azure AI Search | ✅ | ✅ | usgovvirginia, usgovarizona | Semantic ranker availability varies |
| Azure Blob Storage | ✅ | ✅ | All Gov regions | Full feature parity |
| Azure Content Safety | ✅ | ✅ | usgovvirginia | Check latest region availability |
| Managed Identity | ✅ | ✅ | All Gov regions | Full feature parity |
| Azure Monitor | ✅ | ✅ | All Gov regions | Some preview features may be missing |
| Azure Key Vault | ✅ | ✅ | All Gov regions | Full feature parity |
| Container Apps | ✅ | ✅ | usgovvirginia, usgovarizona | Feature availability may lag |
| AKS | ✅ | ✅ | All Gov regions | Full feature parity |

---

## 🌐 Region-Specific Endpoints

- [ ] 🇺🇸 **Azure OpenAI endpoints** use `.azure.us` instead of `.azure.com`
  - Commercial: `https://{name}.openai.azure.com/`
  - Gov: `https://{name}.openai.azure.us/`

- [ ] 🇺🇸 **Azure AI Search endpoints** use `.azure.us` instead of `.windows.net`
  - Commercial: `https://{name}.search.windows.net`
  - Gov: `https://{name}.search.azure.us`

- [ ] 🇺🇸 **Blob Storage endpoints** use `.usgovcloudapi.net` instead of `.core.windows.net`
  - Commercial: `https://{name}.blob.core.windows.net`
  - Gov: `https://{name}.blob.core.usgovcloudapi.net`

- [ ] 🇺🇸 **Entra ID (AAD) authority** uses `.microsoftonline.us`
  - Commercial: `https://login.microsoftonline.com`
  - Gov: `https://login.microsoftonline.us`

- [ ] 🇺🇸 **Azure Resource Manager** endpoint differs
  - Commercial: `https://management.azure.com`
  - Gov: `https://management.usgovcloudapi.net`

- [ ] ✅ **Application code** uses `cloud_mode` config to resolve correct endpoints (see ADR-007)

---

## 🛡️ FedRAMP Compliance Considerations

- [ ] 🔲 **Authorization boundary defined** — document which Azure services are in scope
- [ ] 🔲 **System Security Plan (SSP)** — draft started, maps to NIST 800-53 controls
- [ ] 🔲 **Continuous monitoring** — Azure Monitor + Log Analytics configured for all services
- [ ] 🔲 **Incident response plan** — documented and tested
- [ ] 🔲 **POA&M (Plan of Action & Milestones)** — process established for tracking remediation
- [ ] 🔲 **3PAO assessment** — third-party assessment organization selected (if applicable)
- [ ] 🔲 **FedRAMP authorization level** — determined (Low, Moderate, or High)
- [ ] 🔲 **Azure services used are individually FedRAMP authorized** — verify at [FedRAMP Marketplace](https://marketplace.fedramp.gov/)

---

## 🔒 Network Isolation Requirements

- [ ] **Private Endpoints** configured for all data-plane operations:
  - [ ] Azure OpenAI
  - [ ] PostgreSQL Flexible Server
  - [ ] Azure AI Search
  - [ ] Azure Blob Storage
  - [ ] Content Safety
- [ ] **VNet integration** for compute resources (Container Apps / AKS)
- [ ] **Network Security Groups (NSGs)** restricting traffic between subnets
- [ ] **No public endpoints** in production — all services accessible only via Private Endpoints
- [ ] **DNS resolution** configured for private endpoints (Private DNS Zones)
- [ ] **Egress control** — outbound traffic restricted to required Azure service endpoints
- [ ] **Azure Firewall or NVA** for centralized egress filtering (if required by policy)

---

## 🗺️ Data Residency Requirements

- [ ] 🇺🇸 **All data stored in US Azure Gov regions** (usgovvirginia, usgovarizona, usgovtexas)
- [ ] 🇺🇸 **Azure OpenAI** processes prompts in-region (verify deployment region)
- [ ] 🇺🇸 **Embeddings** are generated and stored within the same region as the data
- [ ] 🇺🇸 **Blob Storage** replication is geo-redundant within Gov regions only (GRS → paired Gov region)
- [ ] 🇺🇸 **PostgreSQL** backups remain within Gov regions
- [ ] 🇺🇸 **No cross-sovereign-cloud data flow** — data never leaves Azure Gov boundary
- [ ] 🇺🇸 **Content Safety** processes text in-region (verify service region matches data region)

---

## 🔑 Identity and Access Management

- [ ] **Managed Identity** used for all service-to-service authentication (no API keys)
- [ ] **RBAC roles** follow principle of least privilege:
  - [ ] `Cognitive Services OpenAI User` for Azure OpenAI access
  - [ ] `Search Index Data Reader` / `Contributor` for AI Search
  - [ ] `Storage Blob Data Reader` / `Contributor` for Blob Storage
  - [ ] `Cognitive Services User` for Content Safety
- [ ] **Entra ID (AAD)** is the sole identity provider for all services
- [ ] **Conditional Access Policies** enforced for interactive users
- [ ] **Privileged Identity Management (PIM)** enabled for administrative roles
- [ ] **Service principal secrets** — none exist (Managed Identity replaces them)
- [ ] **API keys** — disabled where possible; if required, stored in Key Vault with rotation policy
- [ ] **Break-glass accounts** documented and stored securely

---

## 📝 Audit Logging Requirements

- [ ] **Azure Activity Log** enabled and exported to Log Analytics
- [ ] **Diagnostic settings** configured for each service:
  - [ ] Azure OpenAI — request/response logging
  - [ ] PostgreSQL — query logging (pgaudit)
  - [ ] AI Search — query and indexing logs
  - [ ] Blob Storage — read/write/delete logs
  - [ ] Content Safety — analysis logs
- [ ] **Application-level logging** — safety check results, query traces, error logs
- [ ] **Log retention** — meets organizational policy (typically 1 year for FedRAMP)
- [ ] **Log integrity** — logs stored in append-only / immutable storage
- [ ] **SIEM integration** — logs forwarded to organizational SIEM (Sentinel, Splunk, etc.)
- [ ] **Alerting** — configured for security events (failed auth, safety blocks, unusual query patterns)

---

## 🔐 Encryption Requirements

- [ ] **Data at rest:**
  - [ ] PostgreSQL: encrypted with AES-256 (Azure managed or CMK)
  - [ ] Blob Storage: encrypted with AES-256 (Azure managed or CMK)
  - [ ] AI Search: encrypted with AES-256 (Azure managed or CMK)
  - [ ] Customer-Managed Keys (CMK) via Key Vault if required by policy
- [ ] **Data in transit:**
  - [ ] TLS 1.2+ enforced for all API calls
  - [ ] PostgreSQL SSL mode set to `require` or `verify-full`
  - [ ] Minimum TLS version set on Storage Account (`MinimumTlsVersion = TLS1_2`)
- [ ] **Key management:**
  - [ ] Azure Key Vault used for CMK storage
  - [ ] Key rotation policy defined and automated
  - [ ] Key Vault access restricted via RBAC (not access policies)
  - [ ] Key Vault soft-delete and purge protection enabled

---

## 🔀 API Differences Between Commercial and Gov

| API Surface | Difference | Impact |
|---|---|---|
| Azure OpenAI API version | Same API versions, but newer versions may be available in Commercial first | Pin to a known-good API version |
| OpenAI model names | Same model names, but availability differs | Verify model availability before deployment |
| Azure AI Search API | Same API, different base URL | Update endpoint in config |
| Content Safety API | Same API, different base URL | Update endpoint in config |
| Azure SDK (`azure-identity`) | Supports Gov via `authority` parameter | Set in `DefaultAzureCredential` config |
| Terraform AzureRM provider | Supports Gov via `environment = "usgovernment"` | Set in provider config |
| Azure CLI | Supports Gov via `az cloud set --name AzureUSGovernment` | Run before `az login` |

---

## ⚠️ Items That Must Be Verified in a Real Gov Subscription

These items **cannot** be fully validated in Commercial Azure and must be tested in an actual Azure Government subscription:

- [ ] **Endpoint resolution** — all services resolve to `.azure.us` / `.usgovcloudapi.net`
- [ ] **Model availability** — the specific model versions you need are deployed in Gov
- [ ] **Private Endpoint connectivity** — Private DNS and VNet routing work correctly in Gov
- [ ] **Entra ID tenant** — Gov tenant is separate from Commercial tenant; verify federation if needed
- [ ] **RBAC role definitions** — some built-in roles may have different IDs in Gov
- [ ] **Azure Policy** — Gov-specific policies may enforce additional restrictions
- [ ] **Feature flags** — some preview features available in Commercial may not be in Gov
- [ ] **Performance baseline** — latency and throughput may differ between Gov and Commercial
- [ ] **Terraform provider version** — verify the provider version supports all resources in Gov
- [ ] **Billing and quotas** — Gov pricing and quotas differ from Commercial

---

## 🇺🇸 Quick Reference: Azure CLI Gov Setup

```bash
# Switch Azure CLI to Government cloud
az cloud set --name AzureUSGovernment

# Login to Azure Government
az login

# Verify you're in the Gov cloud
az cloud show --query name -o tsv
# Expected: AzureUSGovernment

# List available regions
az account list-locations --query "[].name" -o tsv | grep gov

# Switch back to Commercial (for development)
az cloud set --name AzureCloud
```

## 🇺🇸 Quick Reference: Terraform Gov Configuration

```hcl
provider "azurerm" {
  features {}
  environment = "usgovernment"  # or "public" for Commercial
}
```

## 🇺🇸 Quick Reference: Python SDK Gov Configuration

```python
from azure.identity import DefaultAzureCredential

# For Azure Government
credential = DefaultAzureCredential(
    authority="https://login.microsoftonline.us"
)

# The Azure OpenAI client uses the Gov endpoint automatically
# when you provide the correct base URL
from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint="https://your-resource.openai.azure.us/",
    azure_ad_token_provider=get_token_provider(credential),
    api_version="2024-02-01"
)
```

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — Gov compatibility checklist with endpoint, compliance, and security items |
