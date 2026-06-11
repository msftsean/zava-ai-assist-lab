# ──────────────────────────────────────────────────────────────────────────────
# Module: Managed Identity + Role Assignments
#
# Creates a user-assigned managed identity and grants it the RBAC roles needed
# to access OpenAI, Storage, Search, and PostgreSQL resources.
# ──────────────────────────────────────────────────────────────────────────────

resource "azurerm_user_assigned_identity" "lab" {
  name                = "${var.project_prefix}-identity-${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags
}

# ── Role Assignments ──────────────────────────────────────────────────────────
# Cognitive Services OpenAI User – lets the identity call the OpenAI API.
resource "azurerm_role_assignment" "openai_user" {
  scope                = var.openai_account_id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = azurerm_user_assigned_identity.lab.principal_id
}

# Storage Blob Data Contributor – read/write SOP documents.
resource "azurerm_role_assignment" "storage_blob" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.lab.principal_id
}

# Search Index Data Contributor – manage search indexes.
resource "azurerm_role_assignment" "search_index" {
  scope                = var.search_service_id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azurerm_user_assigned_identity.lab.principal_id
}

# Search Service Contributor – manage search service configuration.
resource "azurerm_role_assignment" "search_service" {
  scope                = var.search_service_id
  role_definition_name = "Search Service Contributor"
  principal_id         = azurerm_user_assigned_identity.lab.principal_id
}

# Contributor on PostgreSQL – needed for Entra-auth integration (if used).
resource "azurerm_role_assignment" "postgres" {
  scope                = var.postgres_server_id
  role_definition_name = "Contributor"
  principal_id         = azurerm_user_assigned_identity.lab.principal_id
}
