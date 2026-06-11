# ──────────────────────────────────────────────────────────────────────────────
# Module: PostgreSQL Flexible Server with pgvector
#
# Provisions a Flexible Server, enables the pgvector extension, and creates a
# database for vector storage.  A firewall rule opens access for the lab
# (0.0.0.0–255.255.255.255).  In production, use VNet integration instead.
# ──────────────────────────────────────────────────────────────────────────────

resource "azurerm_postgresql_flexible_server" "this" {
  name                          = "${var.project_prefix}-pg-${var.suffix}"
  resource_group_name           = var.resource_group_name
  location                      = var.location
  version                       = "16"
  administrator_login           = var.admin_username
  administrator_password        = var.admin_password
  sku_name                      = var.sku_name
  storage_mb                    = 32768
  backup_retention_days         = 7
  geo_redundant_backup_enabled  = false
  public_network_access_enabled = true

  tags = var.tags

  lifecycle {
    ignore_changes = [zone]
  }
}

# Enable pgvector and other useful extensions via server configuration.
resource "azurerm_postgresql_flexible_server_configuration" "extensions" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.this.id
  value     = "VECTOR,UUID-OSSP,PGCRYPTO"
}

# Database for vector storage.
resource "azurerm_postgresql_flexible_server_database" "vectors" {
  name      = "vectordb"
  server_id = azurerm_postgresql_flexible_server.this.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Lab-only firewall rule – allow all Azure services + lab machines.
# Replace with a VNet rule in production.
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_all_lab" {
  name             = "allow-lab-access"
  server_id        = azurerm_postgresql_flexible_server.this.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}
