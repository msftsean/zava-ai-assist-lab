# ──────────────────────────────────────────────────────────────────────────────
# Module: Azure AI Content Safety
#
# Gov note: Content Safety (kind="ContentSafety") availability in Azure Gov
# may be limited.  Verify the service is registered in your subscription and
# available in your target region before deploying.
# ──────────────────────────────────────────────────────────────────────────────

resource "azurerm_cognitive_account" "content_safety" {
  name                  = "${var.project_prefix}-csafety-${var.suffix}"
  resource_group_name   = var.resource_group_name
  location              = var.location
  kind                  = "ContentSafety"
  sku_name              = "S0"
  custom_subdomain_name = "${var.project_prefix}-csafety-${var.suffix}"

  public_network_access_enabled = true

  tags = var.tags
}
