#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# deploy.sh – Validate prerequisites and run Terraform for the AI Assist Lab.
#
# Usage:
#   ./scripts/deploy.sh              # interactive apply (will prompt)
#   ./scripts/deploy.sh --auto       # non-interactive (auto-approve)
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="${SCRIPT_DIR}/../infra"
AUTO_APPROVE=""

if [[ "${1:-}" == "--auto" ]]; then
  AUTO_APPROVE="-auto-approve"
fi

# ── Helpers ───────────────────────────────────────────────────────────────────
info()  { echo -e "\033[1;34m[INFO]\033[0m  $*"; }
warn()  { echo -e "\033[1;33m[WARN]\033[0m  $*"; }
error() { echo -e "\033[1;31m[ERROR]\033[0m $*"; exit 1; }

# ── Check Azure CLI login ────────────────────────────────────────────────────
info "Checking Azure CLI login…"
if ! az account show &>/dev/null; then
  error "Not logged in to Azure CLI. Run 'az login' (or 'az login --use-device-code') first."
fi

CLOUD_NAME=$(az cloud show --query name -o tsv 2>/dev/null || echo "unknown")
info "Azure CLI cloud: ${CLOUD_NAME}"

if [[ "${CLOUD_NAME}" == "AzureUSGovernment" ]]; then
  info "Targeting Azure Government."
elif [[ "${CLOUD_NAME}" == "AzureCloud" ]]; then
  info "Targeting Azure Commercial."
else
  warn "Unexpected cloud name '${CLOUD_NAME}'. Proceeding anyway."
fi

# ── Check Terraform ───────────────────────────────────────────────────────────
if ! command -v terraform &>/dev/null; then
  error "Terraform CLI not found. Install it from https://developer.hashicorp.com/terraform/install"
fi
info "Terraform version: $(terraform version -json | grep -o '"terraform_version":"[^"]*"' | head -1)"

# ── Terraform Workflow ────────────────────────────────────────────────────────
cd "${INFRA_DIR}"

info "Running terraform init…"
terraform init -input=false

info "Running terraform validate…"
terraform validate

info "Running terraform plan…"
terraform plan -out=tfplan

info "Running terraform apply…"
terraform apply ${AUTO_APPROVE} tfplan

# ── Print key outputs ─────────────────────────────────────────────────────────
info "Deployment complete. Key outputs:"
echo ""
terraform output -json | python3 -c "
import json, sys
outputs = json.load(sys.stdin)
for k, v in sorted(outputs.items()):
    val = v.get('value', '<sensitive>')
    if v.get('sensitive'):
        val = '(sensitive – use terraform output <name>)'
    print(f'  {k:40s} = {val}')
" 2>/dev/null || terraform output

# Clean up plan file.
rm -f tfplan
info "Done."
