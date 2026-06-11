# ──────────────────────────────────────────────────────────────────────────────
# Module: Azure Blob Storage – SOP Document Ingestion
#
# Creates a Storage Account and a container named "sop-documents" for lab
# document upload.  Blob versioning is enabled for traceability.
# ──────────────────────────────────────────────────────────────────────────────

resource "azurerm_storage_account" "this" {
  name                     = "${var.project_prefix}stor${var.suffix}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Blob versioning for lab traceability.
  blob_properties {
    versioning_enabled = true
  }

  tags = var.tags
}

resource "azurerm_storage_container" "sop_documents" {
  name                  = "sop-documents"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}
