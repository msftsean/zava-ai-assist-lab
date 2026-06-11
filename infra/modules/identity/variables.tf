variable "resource_group_name" {
  description = "Name of the resource group."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
}

variable "project_prefix" {
  description = "Naming prefix."
  type        = string
}

variable "suffix" {
  description = "Unique suffix for global naming."
  type        = string
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}

# Resource IDs for role-assignment scoping.
variable "openai_account_id" {
  description = "Resource ID of the Azure OpenAI account."
  type        = string
}

variable "storage_account_id" {
  description = "Resource ID of the Storage Account."
  type        = string
}

variable "search_service_id" {
  description = "Resource ID of the Azure AI Search service."
  type        = string
}

variable "postgres_server_id" {
  description = "Resource ID of the PostgreSQL Flexible Server."
  type        = string
}
