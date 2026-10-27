# Versions verified against official HashiCorp releases on 2026-10-26.
# https://releases.hashicorp.com/terraform/1.17.0/
# https://github.com/hashicorp/terraform-provider-azurerm/releases/tag/v5.10.0
terraform {
  required_version = "= 1.17.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "= 5.10.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
}
