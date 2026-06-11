#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# setup-env.sh – Populate environment variables from Terraform outputs.
#
# Source this file to load vars into your shell:
#   source ./scripts/setup-env.sh
#
# It reads outputs from the Terraform state and exports them so downstream
# tools (Python notebooks, app containers, etc.) can consume them.
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"

info() { echo -e "\033[1;34m[INFO]\033[0m  $*"; }

# ── Detect cloud environment ─────────────────────────────────────────────────
CLOUD_NAME=$(az cloud show --query name -o tsv 2>/dev/null || echo "AzureUSGovernment")
if [[ "${CLOUD_NAME}" == "AzureUSGovernment" ]]; then
  export AZURE_CLOUD="AzureUSGovernment"
else
  export AZURE_CLOUD="AzureCloud"
fi
info "AZURE_CLOUD=${AZURE_CLOUD}"

# ── Read Terraform outputs ───────────────────────────────────────────────────
cd "${INFRA_DIR}"
TF_OUT=$(terraform output -json 2>/dev/null)

tf_val() {
  echo "${TF_OUT}" | python3 -c "import json,sys; print(json.load(sys.stdin).get('$1',{}).get('value',''))" 2>/dev/null
}

tf_sensitive() {
  terraform output -raw "$1" 2>/dev/null || echo ""
}

# ── Azure Location ────────────────────────────────────────────────────────────
export AZURE_LOCATION=$(tf_val "resource_group_name" | xargs -I{} az group show -n {} --query location -o tsv 2>/dev/null || echo "usgovvirginia")

# ── OpenAI ────────────────────────────────────────────────────────────────────
export AZURE_OPENAI_ENDPOINT=$(tf_val "openai_endpoint")
export AZURE_OPENAI_KEY=$(tf_sensitive "openai_primary_access_key" 2>/dev/null || echo "<set-manually>")
export AZURE_OPENAI_DEPLOYMENT=$(tf_val "openai_model_deployment_name")

# ── AI Search ─────────────────────────────────────────────────────────────────
export AZURE_SEARCH_ENDPOINT=$(tf_val "ai_search_endpoint")
export AZURE_SEARCH_KEY=$(tf_sensitive "ai_search_primary_key" 2>/dev/null || echo "<set-manually>")

# ── Storage ───────────────────────────────────────────────────────────────────
export AZURE_STORAGE_ACCOUNT=$(tf_val "storage_account_name")
export AZURE_STORAGE_CONTAINER=$(tf_val "storage_container_name")

# ── PostgreSQL ────────────────────────────────────────────────────────────────
export POSTGRES_HOST=$(tf_val "postgresql_fqdn")
export POSTGRES_DB=$(tf_val "postgresql_database_name")
export POSTGRES_USER=$(tf_sensitive "postgresql_admin_username" 2>/dev/null || echo "pgadmin")
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-<set-manually>}"

# ── Content Safety ────────────────────────────────────────────────────────────
export CONTENT_SAFETY_ENDPOINT=$(tf_val "content_safety_endpoint")
export CONTENT_SAFETY_KEY=$(tf_sensitive "content_safety_primary_access_key" 2>/dev/null || echo "<set-manually>")

# ── Summary ───────────────────────────────────────────────────────────────────
info "Environment variables exported:"
env | grep -E '^(AZURE_|POSTGRES_|CONTENT_SAFETY_)' | sort | sed 's/=.*KEY=.*/=<redacted>/' | while read -r line; do
  echo "  ${line}"
done
info "Done. Variables are available in this shell session."
