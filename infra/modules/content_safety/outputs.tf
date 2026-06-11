output "account_id" {
  description = "Resource ID of the Content Safety account."
  value       = azurerm_cognitive_account.content_safety.id
}

output "endpoint" {
  description = "Endpoint URL for the Content Safety service."
  value       = azurerm_cognitive_account.content_safety.endpoint
}

output "primary_access_key" {
  description = "Primary access key (sensitive)."
  value       = azurerm_cognitive_account.content_safety.primary_access_key
  sensitive   = true
}
