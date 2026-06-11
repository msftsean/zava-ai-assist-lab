# ──────────────────────────────────────────────────────────────────────────────
# Provider Configuration
# Pin provider versions so lab participants get reproducible results.
# ──────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.14"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# The azurerm provider `environment` attribute controls which Azure cloud
# endpoints are used.  "usgovernment" → Azure Gov, "public" → Azure Commercial.
provider "azurerm" {
  environment = var.azure_environment
  features {}
}

provider "random" {}
