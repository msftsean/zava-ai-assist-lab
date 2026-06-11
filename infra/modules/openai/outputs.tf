output "account_id" {
  description = "Resource ID of the Azure OpenAI account."
  value       = azurerm_cognitive_account.openai.id
}

output "endpoint" {
  description = "Endpoint URL for the Azure OpenAI service."
  value       = azurerm_cognitive_account.openai.endpoint
}

output "model_deployment_name" {
  description = "Name of the deployed model."
  value       = azurerm_cognitive_deployment.model.name
}

output "primary_access_key" {
  description = "Primary access key (sensitive)."
  value       = azurerm_cognitive_account.openai.primary_access_key
  sensitive   = true
}
