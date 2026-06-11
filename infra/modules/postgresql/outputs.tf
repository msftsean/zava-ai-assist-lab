output "server_id" {
  description = "Resource ID of the PostgreSQL Flexible Server."
  value       = azurerm_postgresql_flexible_server.this.id
}

output "fqdn" {
  description = "Fully-qualified domain name of the server."
  value       = azurerm_postgresql_flexible_server.this.fqdn
}

output "database_name" {
  description = "Name of the vector database."
  value       = azurerm_postgresql_flexible_server_database.vectors.name
}

output "admin_username" {
  description = "Administrator login."
  value       = azurerm_postgresql_flexible_server.this.administrator_login
}
