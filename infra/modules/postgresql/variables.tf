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

variable "admin_username" {
  description = "PostgreSQL administrator login."
  type        = string
}

variable "admin_password" {
  description = "PostgreSQL administrator password."
  type        = string
  sensitive   = true
}

variable "sku_name" {
  description = "SKU for the Flexible Server."
  type        = string
  default     = "GP_Standard_D2s_v3"
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
