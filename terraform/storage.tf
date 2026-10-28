resource "azurerm_storage_account" "inventory" {
  name                            = var.storage_account_name
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  min_tls_version                 = "TLS1_2"
  https_traffic_only_enabled      = true
  shared_access_key_enabled       = false
  default_to_oauth_authentication = true
  allow_nested_items_to_be_public = false

  # Simple classroom setup: public HTTPS endpoint, managed identity authorization.
  # No anonymous access or shared storage keys. Network-policy review is required.
  public_network_access = "Enabled"


  lifecycle {
    prevent_destroy = true
  }

  tags = {
    project    = "warehouse-stock-tracker"
    managed_by = "terraform"
  }
}

resource "azurerm_storage_table" "inventory" {
  name               = "inventory"
  storage_account_id = azurerm_storage_account.inventory.id

  lifecycle {
    prevent_destroy = true
  }
}

resource "azurerm_user_assigned_identity" "app" {
  name                = "id-warehouse-stock-tracker"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_role_assignment" "app_table" {
  scope                = azurerm_storage_table.inventory.resource_manager_id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = azurerm_user_assigned_identity.app.principal_id
  principal_type       = "ServicePrincipal"
}

# Optional: enable az-login authentication for the developer without storage keys.
resource "azurerm_role_assignment" "developer_table" {
  count                = var.developer_object_id == null ? 0 : 1
  scope                = azurerm_storage_table.inventory.resource_manager_id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = var.developer_object_id
  principal_type       = "User"
}
