output "identity_id" {
  description = "Resource ID of the user-assigned managed identity."
  value       = azurerm_user_assigned_identity.lab.id
}

output "client_id" {
  description = "Client (application) ID of the managed identity."
  value       = azurerm_user_assigned_identity.lab.client_id
}

output "principal_id" {
  description = "Principal (object) ID of the managed identity."
  value       = azurerm_user_assigned_identity.lab.principal_id
}
