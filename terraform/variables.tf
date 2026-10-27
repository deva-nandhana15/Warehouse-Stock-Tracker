# Deployment inputs only. Supply credentials through the owner's environment.
# Never put tokens, passwords or private keys in these files.

variable "azure_subscription_id" {
  description = "Azure subscription ID (pass via TF_VAR or an uncommitted .tfvars file)."
  type        = string
  sensitive   = true
}

variable "resource_group_name" {
  description = "Name of the Azure Resource Group."
  type        = string
  default     = "rg-warehouse-stock-tracker"
}

variable "location" {
  description = "Azure region for all resources."
  type        = string
  default     = "centralindia"
}

variable "container_image" {
  description = "Docker Hub image without tag (e.g. dva15/warehouse-stock-tracker)."
  type        = string
  default     = "dva15/warehouse-stock-tracker"
}

variable "container_image_tag" {
  description = "Full Git commit SHA of the image that passed all CI gates."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-f]{40}$", var.container_image_tag))
    error_message = "Use the full 40-character lowercase Git commit SHA; dev and latest are not deployment tags."
  }
}

variable "dns_label" {
  description = "DNS label for the container group. Must be unique within the region."
  type        = string
  default     = "warehouse-stock-tracker"
}

variable "container_port" {
  description = "Port exposed by the container."
  type        = number
  default     = 5000
}

variable "container_cpu" {
  description = "CPU cores. This single-container group requires at least 1 CPU."
  type        = number
  default     = 1

  validation {
    condition     = var.container_cpu >= 1
    error_message = "Allocate at least 1 CPU to this single-container ACI group."
  }
}

variable "container_memory" {
  description = "Memory in GB. This single-container group requires at least 1 GB."
  type        = number
  default     = 1

  validation {
    condition     = var.container_memory >= 1
    error_message = "Allocate at least 1 GB to this single-container ACI group."
  }
}

variable "storage_account_name" {
  description = "Globally unique Azure Storage account name: 3-24 lowercase letters/digits."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "Use 3-24 lowercase letters and digits for the storage account name."
  }
}

variable "developer_object_id" {
  description = "Optional Entra user object ID to grant local az-login access to inventory data."
  type        = string
  default     = null
  nullable    = true
}
