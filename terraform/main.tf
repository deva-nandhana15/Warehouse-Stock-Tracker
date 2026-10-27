# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    project     = "warehouse-stock-tracker"
    environment = "dev"
    managed_by  = "terraform"
  }
}

# Single-container ACI group: minimum 1 CPU and 1 GB total.
# Non-root execution is configured by USER 10001:10001 in the Dockerfile.
# AzureRM 5.10.0 arguments checked against the provider's versioned docs.
resource "azurerm_container_group" "app" {
  name                = "ci-warehouse-stock-tracker"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  ip_address_type     = "Public"
  dns_name_label      = var.dns_label
  restart_policy      = "Always"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app.id]
  }

  depends_on = [azurerm_role_assignment.app_table]

  container {
    name   = "warehouse-api"
    image  = "${var.container_image}:${var.container_image_tag}"
    cpu    = var.container_cpu
    memory = var.container_memory

    ports {
      port     = var.container_port
      protocol = "TCP"
    }

    environment_variables = {
      APP_VERSION          = var.container_image_tag
      PORT                 = tostring(var.container_port)
      STORAGE_BACKEND      = "azure-table"
      AZURE_AUTH_MODE      = "managed-identity"
      AZURE_TABLE_ENDPOINT = azurerm_storage_account.inventory.primary_table_endpoint
      AZURE_TABLE_NAME     = azurerm_storage_table.inventory.name
      AZURE_CLIENT_ID      = azurerm_user_assigned_identity.app.client_id
    }

    # Liveness probe matches the Dockerfile HEALTHCHECK.
    liveness_probe {
      http_get {
        path   = "/health"
        port   = var.container_port
        scheme = "Http"
      }
      initial_delay_seconds = 10
      period_seconds        = 30
      timeout_seconds       = 5
      failure_threshold     = 3
    }
  }

  tags = {
    project     = "warehouse-stock-tracker"
    environment = "dev"
    managed_by  = "terraform"
  }
}
