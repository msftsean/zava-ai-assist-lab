output "search_service_id" {
  description = "Resource ID of the Azure AI Search service."
  value       = azurerm_search_service.this.id
}

output "endpoint" {
  description = "Endpoint URL (https://<name>.search.windows.us for Gov)."
  value       = "https://${azurerm_search_service.this.name}.search.windows.us"
}

output "primary_key" {
  description = "Primary admin key (sensitive)."
  value       = azurerm_search_service.this.primary_key
  sensitive   = true
}

output "name" {
  description = "Name of the search service."
  value       = azurerm_search_service.this.name
}
