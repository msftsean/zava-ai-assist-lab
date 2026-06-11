output "storage_account_id" {
  description = "Resource ID of the Storage Account."
  value       = azurerm_storage_account.this.id
}

output "storage_account_name" {
  description = "Name of the Storage Account."
  value       = azurerm_storage_account.this.name
}

output "container_name" {
  description = "Name of the SOP documents container."
  value       = azurerm_storage_container.sop_documents.name
}

output "primary_blob_endpoint" {
  description = "Primary blob endpoint."
  value       = azurerm_storage_account.this.primary_blob_endpoint
}

output "primary_access_key" {
  description = "Primary access key (sensitive)."
  value       = azurerm_storage_account.this.primary_access_key
  sensitive   = true
}
