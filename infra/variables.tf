# ──────────────────────────────────────────────────────────────────────────────
# Zava Hands-on Lab – Root Variables
# Supports AzureUSGovernment (default) and AzureCloud via parameterisation.
# ──────────────────────────────────────────────────────────────────────────────

variable "azure_environment" {
  description = "Azure cloud environment. Use 'usgovernment' for Azure Gov or 'public' for Azure Commercial."
  type        = string
  default     = "usgovernment"

  validation {
    condition     = contains(["usgovernment", "public"], var.azure_environment)
    error_message = "azure_environment must be 'usgovernment' or 'public'."
  }
}

variable "location" {
  description = "Azure region for all resources. Default targets Azure Gov Virginia."
  type        = string
  default     = "usgovvirginia"
}

variable "project_prefix" {
  description = "Short prefix used to name all lab resources (lowercase, no special chars)."
  type        = string
  default     = "zavaailab"
}

variable "resource_group_name" {
  description = "Name of the resource group that will contain all lab resources."
  type        = string
  default     = "rg-zavaailab"
}

variable "openai_model_name" {
  description = "Azure OpenAI model to deploy (must be available in target cloud/region)."
  type        = string
  default     = "gpt-4.1"
}

variable "openai_model_version" {
  description = "Version of the OpenAI model to deploy. Check regional availability."
  type        = string
  default     = "2024-05-13"
}

variable "postgres_admin_username" {
  description = "Administrator login for the PostgreSQL Flexible Server."
  type        = string
  default     = "pgadmin"
}

variable "postgres_admin_password" {
  description = "Administrator password for the PostgreSQL Flexible Server."
  type        = string
  sensitive   = true
}

variable "postgres_sku" {
  description = "SKU for the PostgreSQL Flexible Server (GP_Standard_D2s_v3 works in Gov)."
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "tags" {
  description = "Common tags applied to every resource for lab identification."
  type        = map(string)
  default = {
    project     = "zava-ai-assist-lab"
    environment = "lab"
    managed_by  = "terraform"
  }
}
