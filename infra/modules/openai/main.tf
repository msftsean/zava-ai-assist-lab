# ──────────────────────────────────────────────────────────────────────────────
# Module: Azure OpenAI (Cognitive Services kind=OpenAI)
#
# Gov note: Azure OpenAI is available in select Gov regions.  A
# custom_subdomain_name is REQUIRED for token-based auth in Gov.
# ──────────────────────────────────────────────────────────────────────────────

resource "azurerm_cognitive_account" "openai" {
  name                = "${var.project_prefix}-openai-${var.suffix}"
  resource_group_name = var.resource_group_name
  location            = var.location
  kind                = "OpenAI"
  sku_name            = "S0"

  # custom_subdomain_name is mandatory for Azure Gov OpenAI deployments.
  custom_subdomain_name = "${var.project_prefix}-openai-${var.suffix}"

  # Public network access – acceptable for lab; restrict in production.
  public_network_access_enabled = true

  tags = var.tags
}

resource "azurerm_cognitive_deployment" "model" {
  name                 = var.model_name
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = var.model_name
    version = var.model_version
  }

  sku {
    name     = "GlobalStandard"
    capacity = 10 # tokens-per-minute in thousands – keep low for lab
  }
}
