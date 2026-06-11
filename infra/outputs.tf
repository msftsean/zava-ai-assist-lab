# ──────────────────────────────────────────────────────────────────────────────
# Root Outputs – Surface key resource IDs and endpoints for lab consumption.
# ──────────────────────────────────────────────────────────────────────────────

# ── Resource Group ────────────────────────────────────────────────────────────
output "resource_group_name" {
  description = "Name of the lab resource group."
  value       = azurerm_resource_group.lab.name
}

output "resource_group_id" {
  description = "Resource ID of the lab resource group."
  value       = azurerm_resource_group.lab.id
}

# ── OpenAI ────────────────────────────────────────────────────────────────────
output "openai_account_id" {
  description = "Resource ID of the Azure OpenAI Cognitive Services account."
  value       = module.openai.account_id
}

output "openai_endpoint" {
  description = "Endpoint URL for the Azure OpenAI service."
  value       = module.openai.endpoint
}

output "openai_model_deployment_name" {
  description = "Name of the deployed OpenAI model."
  value       = module.openai.model_deployment_name
}

# ── PostgreSQL ────────────────────────────────────────────────────────────────
output "postgresql_server_id" {
  description = "Resource ID of the PostgreSQL Flexible Server."
  value       = module.postgresql.server_id
}

output "postgresql_fqdn" {
  description = "FQDN of the PostgreSQL Flexible Server."
  value       = module.postgresql.fqdn
}

output "postgresql_database_name" {
  description = "Name of the vector database."
  value       = module.postgresql.database_name
}

# ── AI Search ─────────────────────────────────────────────────────────────────
output "ai_search_service_id" {
  description = "Resource ID of the Azure AI Search service."
  value       = module.ai_search.search_service_id
}

output "ai_search_endpoint" {
  description = "Endpoint URL of the Azure AI Search service."
  value       = module.ai_search.endpoint
}

# ── Storage ───────────────────────────────────────────────────────────────────
output "storage_account_id" {
  description = "Resource ID of the Storage Account."
  value       = module.storage.storage_account_id
}

output "storage_account_name" {
  description = "Name of the Storage Account."
  value       = module.storage.storage_account_name
}

output "storage_container_name" {
  description = "Name of the SOP documents blob container."
  value       = module.storage.container_name
}

# ── Content Safety ────────────────────────────────────────────────────────────
output "content_safety_account_id" {
  description = "Resource ID of the Content Safety Cognitive Services account."
  value       = module.content_safety.account_id
}

output "content_safety_endpoint" {
  description = "Endpoint URL for the Content Safety service."
  value       = module.content_safety.endpoint
}

# ── Managed Identity ──────────────────────────────────────────────────────────
output "managed_identity_id" {
  description = "Resource ID of the user-assigned managed identity."
  value       = module.identity.identity_id
}

output "managed_identity_client_id" {
  description = "Client ID of the user-assigned managed identity."
  value       = module.identity.client_id
}

output "managed_identity_principal_id" {
  description = "Principal (object) ID of the managed identity."
  value       = module.identity.principal_id
}

# ── AKS ───────────────────────────────────────────────────────────────────────
output "aks_cluster_id" {
  description = "Resource ID of the AKS cluster."
  value       = module.aks.cluster_id
}

output "aks_cluster_name" {
  description = "Name of the AKS cluster."
  value       = module.aks.cluster_name
}
