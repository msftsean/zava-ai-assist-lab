# ──────────────────────────────────────────────────────────────────────────────
# Zava Hands-on Lab: Azure Gov AI Assist – Root Module
#
# One codebase, two clouds.  Set `azure_environment` to "usgovernment" (default)
# or "public" to target Azure Government or Azure Commercial respectively.
# ──────────────────────────────────────────────────────────────────────────────

# ── Resource Group ────────────────────────────────────────────────────────────
resource "azurerm_resource_group" "lab" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# ── Unique suffix for globally-unique names ───────────────────────────────────
resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

locals {
  # Short unique suffix keeps resource names globally unique in the lab.
  suffix = random_string.suffix.result
}

# ── Managed Identity ─────────────────────────────────────────────────────────
module "identity" {
  source = "./modules/identity"

  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  project_prefix      = var.project_prefix
  suffix              = local.suffix
  tags                = var.tags

  # Pass resource IDs so role assignments can be created.
  openai_account_id  = module.openai.account_id
  search_service_id  = module.ai_search.search_service_id
  storage_account_id = module.storage.storage_account_id
  postgres_server_id = module.postgresql.server_id
}

# ── Azure OpenAI ──────────────────────────────────────────────────────────────
module "openai" {
  source = "./modules/openai"

  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  project_prefix      = var.project_prefix
  suffix              = local.suffix
  model_name          = var.openai_model_name
  model_version       = var.openai_model_version
  tags                = var.tags
}

# ── PostgreSQL (pgvector) ─────────────────────────────────────────────────────
module "postgresql" {
  source = "./modules/postgresql"

  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  project_prefix      = var.project_prefix
  suffix              = local.suffix
  admin_username      = var.postgres_admin_username
  admin_password      = var.postgres_admin_password
  sku_name            = var.postgres_sku
  tags                = var.tags
}

# ── Azure AI Search ───────────────────────────────────────────────────────────
module "ai_search" {
  source = "./modules/ai_search"

  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  project_prefix      = var.project_prefix
  suffix              = local.suffix
  tags                = var.tags
}

# ── Blob Storage (SOP document ingestion) ─────────────────────────────────────
module "storage" {
  source = "./modules/storage"

  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  project_prefix      = var.project_prefix
  suffix              = local.suffix
  tags                = var.tags
}

# ── Azure AI Content Safety ───────────────────────────────────────────────────
module "content_safety" {
  source = "./modules/content_safety"

  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  project_prefix      = var.project_prefix
  suffix              = local.suffix
  tags                = var.tags
}

# ── AKS (stub) ────────────────────────────────────────────────────────────────
module "aks" {
  source = "./modules/aks"

  resource_group_name = azurerm_resource_group.lab.name
  location            = azurerm_resource_group.lab.location
  project_prefix      = var.project_prefix
  suffix              = local.suffix
  tags                = var.tags
}
