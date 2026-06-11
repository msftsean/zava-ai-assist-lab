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
