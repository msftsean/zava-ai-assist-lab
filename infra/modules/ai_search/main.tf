# ──────────────────────────────────────────────────────────────────────────────
# Module: Azure AI Search (formerly Cognitive Search)
#
# Gov note: Azure AI Search is available in select Gov regions (usgovvirginia,
# usgovarizona).  Use "basic" SKU for the lab to minimise cost.
# ──────────────────────────────────────────────────────────────────────────────

resource "azurerm_search_service" "this" {
  name                = "${var.project_prefix}-search-${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "basic"

  # Public access is fine for a lab; disable in production.
  public_network_access_enabled = true

  tags = var.tags
}
