# 🔧 Troubleshooting Guide

> 📊 **Status:** ████████████████████ 100% Complete | 🏷️ **Version:** 1.1.0 | 📅 **Updated:** 2026-03-10

This guide covers common issues encountered during the AI Assist lab, organized by phase. For each issue, we provide 🔴 symptoms, 🟡 likely causes, and 🟢 resolution steps.

---

## 🔧 Phase 1: Infrastructure Provisioning

### ⚡ Terraform Errors

#### `Error: Quota exceeded for resource type`

🔴 **Symptoms:**
```
Error: creating Cognitive Account: unexpected status 409 with error:
  QuotaExceeded: Operation could not be completed as it results in exceeding
  approved quota.
```

🟡 **Cause:** Your subscription has hit the quota limit for Azure OpenAI accounts, PostgreSQL servers, or other resources.

🟢 **Fix:**
```bash
# Check current quota usage
az cognitiveservices account list --query "[].{name:name, kind:kind}" -o table

# Option 1: Delete unused resources
az cognitiveservices account delete --name <unused-resource> --resource-group <rg>

# Option 2: Use a different region
# Edit infra/terraform.tfvars:
#   azure_region = "westus2"  # try a different region

# Option 3: Request a quota increase via Azure Portal
# Portal → Subscriptions → Usage + quotas → Request increase
```

---

#### `Error: Resource already exists`

🔴 **Symptoms:**
```
Error: A resource with the ID "/subscriptions/.../resourceGroups/rg-aiassist-lab"
  already exists.
```

🟡 **Cause:** A previous deployment created this resource and Terraform state doesn't know about it.

🟢 **Fix:**
```bash
# Option 1: Import the existing resource into Terraform state
terraform import azurerm_resource_group.main /subscriptions/<sub-id>/resourceGroups/rg-aiassist-lab

# Option 2: Use a different name
# Edit infra/terraform.tfvars:
#   project_name = "aiassist2"

# Option 3: Delete the existing resource (if it's from a previous lab attempt)
az group delete --name rg-aiassist-lab --yes --no-wait
# Wait for deletion to complete, then re-run terraform apply
```

---

#### `Error: Provider authentication failed`

🔴 **Symptoms:**
```
Error: building AzureRM Client: Authenticating using the Azure CLI is only
  supported as a User (not a Service Principal).
```

🟡 **Cause:** Azure CLI session has expired or you're not logged in.

🟢 **Fix:**
```bash
# Re-authenticate
az login

# If using a specific subscription
az account set --subscription "<subscription-name-or-id>"

# Verify
az account show --query "{name:name, id:id}" -o table
```

---

#### `Error: API version not supported`

🔴 **Symptoms:**
```
Error: creating resource: the API version 2024-xx-xx is not supported
```

🟡 **Cause:** The AzureRM Terraform provider version is outdated.

🟢 **Fix:**
```bash
# Update the provider
cd infra
terraform init -upgrade

# If that doesn't work, pin a specific provider version in infra/versions.tf:
# terraform {
#   required_providers {
#     azurerm = {
#       source  = "hashicorp/azurerm"
#       version = "~> 3.85"
#     }
#   }
# }
```

---

### 🔑 Azure CLI Authentication Issues

#### `az login` hangs or fails

🔴 **Symptoms:** Browser doesn't open, or device code flow hangs.

🟢 **Fix:**
```bash
# Use device code flow (works in headless/remote environments)
az login --use-device-code

# For managed environments (Codespaces, Cloud Shell)
az login --identity  # if Managed Identity is available

# Clear cached credentials and retry
az account clear
az login
```

---

#### Wrong subscription selected

🔴 **Symptoms:** Resources deploy to an unexpected subscription.

🟢 **Fix:**
```bash
# List all subscriptions
az account list --query "[].{name:name, id:id, isDefault:isDefault}" -o table

# Set the correct subscription
az account set --subscription "<correct-subscription-id>"

# Verify
az account show --query name -o tsv
```

---

## 📄 Phase 2: Ingestion & Indexing

### 🗄️ PostgreSQL Connection Issues

#### `Connection refused` or `Connection timed out`

🔴 **Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
  Is the server running on host "psql-aiassist-lab.postgres.database.azure.com"
  and accepting TCP/IP connections on port 5432?
```

🟡 **Cause:** Firewall rules don't allow your IP address.

🟢 **Fix:**
```bash
# Add your current IP to the firewall
MY_IP=$(curl -s ifconfig.me)
az postgres flexible-server firewall-rule create \
  --resource-group rg-aiassist-lab \
  --name psql-aiassist-lab \
  --rule-name allow-my-ip \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP

# Or allow all Azure services (for lab purposes only)
az postgres flexible-server firewall-rule create \
  --resource-group rg-aiassist-lab \
  --name psql-aiassist-lab \
  --rule-name allow-azure \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

---

#### `Permission denied for schema public`

🔴 **Symptoms:**
```
psycopg2.errors.InsufficientPrivilege: permission denied for schema public
```

🟡 **Cause:** AAD user doesn't have the required PostgreSQL roles.

🟢 **Fix:**
```sql
-- Connect as the PostgreSQL admin and grant permissions
GRANT ALL ON SCHEMA public TO "<your-aad-user>";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "<your-aad-user>";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "<your-aad-user>";
```

---

### 🧩 pgvector Extension Issues

#### `Extension "vector" is not available`

🔴 **Symptoms:**
```
ERROR: extension "vector" is not available
DETAIL: Could not open extension control file
```

🟡 **Cause:** The `vector` extension is not allowlisted in the PostgreSQL server configuration.

🟢 **Fix:**
```bash
# Enable the vector extension via server parameter
az postgres flexible-server parameter set \
  --resource-group rg-aiassist-lab \
  --server-name psql-aiassist-lab \
  --name azure.extensions \
  --value "vector"

# Then connect to PostgreSQL and create the extension
# psql> CREATE EXTENSION IF NOT EXISTS vector;
```

---

#### `Wrong vector dimensions`

🔴 **Symptoms:**
```
ERROR: expected 1536 dimensions, not 768
```

🟡 **Cause:** The embedding model produced vectors with a different dimension than the table expects.

🟢 **Fix:**
```bash
# Check which embedding model you're using
# text-embedding-ada-002 → 1536 dimensions
# text-embedding-3-small → 1536 dimensions (default) or custom
# text-embedding-3-large → 3072 dimensions (default) or custom

# Verify your column definition matches your model
# psql> \d sop_chunks
# The embedding column should be: vector(1536)
```

---

### 🔎 AI Search Indexing Failures

#### `Index not found`

🔴 **Symptoms:**
```
azure.core.exceptions.ResourceNotFoundError: (IndexNotFound) The index
  'sops-index' was not found.
```

🟡 **Cause:** The index hasn't been created yet, or the name doesn't match.

🟢 **Fix:**
```bash
# List existing indexes
az search index list \
  --service-name srch-aiassist-lab \
  --resource-group rg-aiassist-lab \
  --query "[].name" -o tsv

# If no index exists, the indexing script should create it.
# Re-run the indexing step:
python -m app.indexing.search_index \
  --search-service srch-aiassist-lab \
  --index-name sops-index \
  --create-if-missing
```

---

#### `Document upload failed (400 Bad Request)`

🔴 **Symptoms:**
```
azure.core.exceptions.HttpResponseError: (400) A document in the request
  could not be indexed.
```

🟡 **Cause:** A field value doesn't match the index schema (e.g., wrong data type, missing required field).

🟢 **Fix:**
```bash
# Check the error details — the API response includes which document failed
# and which field caused the issue.

# Common causes:
# 1. chunk_id contains characters not allowed in keys (use alphanumeric + hyphens)
# 2. embedding field is null or wrong dimension
# 3. A required field is missing from the document

# Fix the document and retry
```

---

## 🔍 Phase 3: RAG Query Flow

### 🤖 OpenAI API Errors

#### `429 Too Many Requests`

🔴 **Symptoms:**
```
openai.RateLimitError: Error code: 429 - Rate limit reached for
  gpt-4o in organization org-xxx on tokens per min (TPM).
```

🟡 **Cause:** You've exceeded the tokens-per-minute rate limit for your Azure OpenAI deployment.

🟢 **Fix:**
```bash
# Option 1: Wait 60 seconds and retry
sleep 60

# Option 2: Reduce batch size or concurrent requests
# In the eval harness, use --concurrency 1

# Option 3: Increase the TPM quota
az cognitiveservices account deployment show \
  --name oai-aiassist-lab \
  --resource-group rg-aiassist-lab \
  --deployment-name gpt-4o \
  --query "properties.rateLimits" -o table
# Increase via Azure Portal → Azure OpenAI → Deployments → Edit
```

---

#### `Model not found`

🔴 **Symptoms:**
```
openai.NotFoundError: Error code: 404 - The API deployment for this resource
  does not exist.
```

🟡 **Cause:** The deployment name doesn't match what's configured in your application.

🟢 **Fix:**
```bash
# List all deployments
az cognitiveservices account deployment list \
  --name oai-aiassist-lab \
  --resource-group rg-aiassist-lab \
  --query "[].{name:name, model:properties.model.name}" -o table

# Use the exact deployment name from the list in your config
```

---

#### `Content filter triggered`

🔴 **Symptoms:**
```
openai.BadRequestError: Error code: content_filter - The response was filtered
  due to the prompt triggering Azure OpenAI's content management policy.
```

🟡 **Cause:** Azure OpenAI's built-in content filter blocked the request or response.

🟢 **Fix:**
- Review the query — it may contain terms that trigger the filter
- This is *different* from our application-level Content Safety checks
- For legitimate queries that are being falsely blocked, consider adjusting the Azure OpenAI content filter settings in the Azure Portal
- Note: In Gov environments, content filter settings may have minimum thresholds that can't be lowered

---

## 🛡️ Phase 4: Content Safety

### 🔌 Content Safety API Errors

#### `Endpoint not found`

🔴 **Symptoms:**
```
azure.core.exceptions.ServiceRequestError: Could not resolve host:
  cs-aiassist-lab.cognitiveservices.azure.com
```

🟡 **Cause:** Wrong endpoint format for Content Safety.

🟢 **Fix:**
```bash
# Get the correct endpoint
az cognitiveservices account show \
  --name cs-aiassist-lab \
  --resource-group rg-aiassist-lab \
  --query "properties.endpoint" -o tsv

# Use this exact endpoint in your configuration
```

---

#### `Access denied (401/403)`

🔴 **Symptoms:**
```
azure.core.exceptions.ClientAuthenticationError: (401) Access denied due to
  invalid subscription key or wrong API endpoint.
```

🟡 **Cause:** Managed Identity doesn't have the correct RBAC role.

🟢 **Fix:**
```bash
# Assign the Cognitive Services User role
IDENTITY_PRINCIPAL_ID=$(az identity show \
  --name id-aiassist-lab \
  --resource-group rg-aiassist-lab \
  --query principalId -o tsv)

CS_RESOURCE_ID=$(az cognitiveservices account show \
  --name cs-aiassist-lab \
  --resource-group rg-aiassist-lab \
  --query id -o tsv)

az role assignment create \
  --assignee $IDENTITY_PRINCIPAL_ID \
  --role "Cognitive Services User" \
  --scope $CS_RESOURCE_ID
```

---

### 🔌 Content Safety API Response Shape

#### `AttributeError: 'AnalyzeTextResult' has no attribute 'hate_result'`

🔴 **Symptoms:**
```
AttributeError: 'AnalyzeTextResult' object has no attribute 'hate_result'
```

🟡 **Cause:** The Content Safety API response structure changed. Results are returned in `result.categories_analysis` (a list of dicts), not as individual attributes like `result.hate_result`.

🟢 **Fix:**
```python
# ❌ WRONG — old API shape (no longer works)
hate_severity = result.hate_result.severity
violence_severity = result.violence_result.severity

# ✅ CORRECT — current API shape
for item in result.categories_analysis:
    # item.category may be an enum or string — handle both
    category = item.category.value if hasattr(item.category, "value") else item.category
    severity = item.severity
    print(f"  {category}: severity {severity}")
```

The response looks like:
```python
result.categories_analysis = [
    {"category": "Hate",     "severity": 0},
    {"category": "Violence", "severity": 2},
    {"category": "SelfHarm", "severity": 0},
    {"category": "Sexual",   "severity": 0},
]
```

> **📝 Note:** The `.category` field may be an enum (`TextCategory.HATE`) or a string (`"Hate"`) depending on the SDK version. Always use `hasattr(item.category, "value")` to handle both cases safely.

---

#### Content Safety passes prompt injection attempts

🔴 **Symptoms:**
Prompt injection text like "Ignore all previous instructions" scores severity 0 across all categories.

🟡 **Cause:** This is **expected behavior**. Azure Content Safety analyzes content **toxicity** (hate, violence, self-harm, sexual), not prompt injection **intent**. A prompt injection that uses non-toxic language will always pass Content Safety.

🟢 **Fix:**
```python
# Content Safety alone is NOT sufficient for injection detection.
# Use the Prompt Shield for injection detection:
from app.safety.prompt_shield import scan_for_injection

result = scan_for_injection(user_input)
if result.is_injection:
    print(f"⚠️ Injection detected: {result.confidence} confidence")
    print(f"  Patterns: {result.matched_patterns}")
    # Block the request or flag for review
```

For the full defense-in-depth approach, use **both**:
1. **Content Safety** → checks for toxic content (hate, violence, etc.)
2. **Prompt Shield** → checks for injection intent (role manipulation, instruction override, etc.)

See `app/safety/prompt_shield.py` for implementation details, and ADR-009 in [Architecture Decisions](architecture-decisions.md) for the rationale.

> **📝 Note:** Azure AI Prompt Shields (preview) is a cloud-based injection detection service. When it reaches GA, integrate it alongside or in place of the pattern-based Prompt Shield.

---

#### Wrong filter profile causing unexpected blocks

🔴 **Symptoms:** Legitimate content is being blocked, or harmful content is being allowed through.

🟡 **Cause:** The wrong filter profile is active for your deployment context.

🟢 **Fix:**
```python
from app.safety.filter_profiles import get_profile, evaluate_all_profiles

# Check which profile is active and its thresholds
print(get_profile("strict"))    # {'hate': 1, 'violence': 1, 'self_harm': 1, 'sexual': 1}
print(get_profile("standard"))  # {'hate': 2, 'violence': 2, 'self_harm': 2, 'sexual': 2}
print(get_profile("relaxed"))   # {'hate': 4, 'violence': 4, 'self_harm': 4, 'sexual': 4}

# Evaluate all profiles against the same scores to diagnose
scores = {"hate": 0, "violence": 2, "self_harm": 0, "sexual": 0}
for name, result in evaluate_all_profiles(scores).items():
    status = "BLOCKED" if result.blocked else "PASS"
    print(f"  {name}: {status}")
# Output:
#   strict: BLOCKED (violence=2 ≥ threshold=1)
#   standard: PASS
#   relaxed: PASS
```

Use `strict` for Gov/FedRAMP, `standard` for enterprise, `relaxed` for dev/test.

---

## 🖥️ General Issues

### 🐳 Docker / Container Issues

#### `Cannot connect to the Docker daemon`

🔴 **Symptoms:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock.
Is the docker daemon running?
```

🟢 **Fix:**
```bash
# Start Docker
sudo systemctl start docker

# Or if using Docker Desktop, launch it from the application menu

# Verify
docker ps
```

---

#### `Image build fails`

🔴 **Symptoms:** `docker build` fails with dependency errors.

🟢 **Fix:**
```bash
# Clear Docker cache and rebuild
docker build --no-cache -t ai-assist .

# If Python dependencies fail, try:
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 🌐 Network / Firewall Issues

#### `SSL: CERTIFICATE_VERIFY_FAILED`

🔴 **Symptoms:**
```
ssl.SSLCertificateVerifyError: [SSL: CERTIFICATE_VERIFY_FAILED]
  certificate verify failed: unable to get local issuer certificate
```

🟡 **Cause:** Corporate proxy or firewall is intercepting HTTPS traffic with its own certificate.

🟢 **Fix:**
```bash
# Option 1: Add corporate CA cert to the trust store
export REQUESTS_CA_BUNDLE=/path/to/corporate-ca-bundle.crt

# Option 2: For Azure CLI specifically
export AZURE_CLI_DISABLE_CONNECTION_VERIFICATION=1  # NOT for production!

# Option 3: Install the corporate CA cert system-wide
sudo cp corporate-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

---

#### `Connection timeout to Azure services`

🔴 **Symptoms:** Azure CLI commands or API calls hang and eventually timeout.

🟡 **Cause:** Firewall or proxy blocking outbound HTTPS (port 443) to Azure endpoints.

🟢 **Fix:**
```bash
# Test connectivity
curl -v https://management.azure.com/  # Should get a response (even 401)
curl -v https://login.microsoftonline.com/  # Should get a response

# If blocked, work with your network team to allowlist:
# - *.azure.com
# - *.microsoftonline.com
# - *.azure.us (if using Gov)
# - *.windows.net

# Or use a VPN / direct connection that bypasses the proxy
```

---

### 🐍 Python Dependency Issues

#### `ModuleNotFoundError`

🔴 **Symptoms:**
```
ModuleNotFoundError: No module named 'openai'
```

🟢 **Fix:**
```bash
# Install dependencies
pip install -r requirements.txt

# If using a virtual environment, make sure it's activated
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Verify
python -c "import openai; print(openai.__version__)"
```

---

#### `Version conflict`

🔴 **Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the
  packages that are installed.
```

🟢 **Fix:**
```bash
# Create a fresh virtual environment
python -m venv .venv --clear
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ⚡ Quick Diagnostic Commands

Use these commands to quickly diagnose common issues:

```bash
# === Environment ===
python --version                    # Should be 3.11+
az version                          # Should be 2.50+
terraform version                   # Should be 1.5+

# === Azure Authentication ===
az account show                     # Currently logged-in account
az account list -o table            # All available subscriptions

# === Resource Status ===
az resource list \
  --resource-group rg-aiassist-lab \
  --query "[].{Name:name, Type:type, State:provisioningState}" \
  -o table

# === Network Connectivity ===
curl -s -o /dev/null -w "%{http_code}" https://management.azure.com/
curl -s -o /dev/null -w "%{http_code}" https://login.microsoftonline.com/

# === PostgreSQL Connectivity ===
pg_isready -h psql-aiassist-lab.postgres.database.azure.com -p 5432

# === Python Environment ===
pip list | grep -E "openai|azure|psycopg2|tiktoken"
```

---

## 🆘 Still Stuck?

1. **Check the error message carefully** — Azure error messages usually include an error code and correlation ID that can be searched in Azure documentation.
2. **Check Azure Service Health** — [status.azure.com](https://status.azure.com/) for outages.
3. **Check Azure CLI version** — many issues are resolved by updating: `az upgrade`.
4. **Ask the facilitator** — they've seen these issues before.
5. **Pair up** — work with a neighbor whose environment is working while debugging yours.

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — troubleshooting for all 5 lab phases |
| 1.1.0 | 2026-03-10 | Squad (Beacon 🔦) | Added Content Safety API response shape issues, prompt injection detection gap, filter profile troubleshooting |
