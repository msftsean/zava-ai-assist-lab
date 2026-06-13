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

variable "model_name" {
  description = "OpenAI model to deploy (e.g. gpt-4.1)."
  type        = string
  default     = "gpt-4.1"
}

variable "model_version" {
  description = "Model version string."
  type        = string
  default     = "2024-05-13"
}

variable "tags" {
  description = "Resource tags."
  type        = map(string)
  default     = {}
}
