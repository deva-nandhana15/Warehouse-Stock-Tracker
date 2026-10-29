# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Outputs â€“ used by CI/CD for smoke tests
# â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

output "app_url" {
  description = "Public classroom demonstration URL for the application."
  value       = "http://${azurerm_container_group.app.fqdn}:${var.container_port}"
}

output "app_fqdn" {
  description = "FQDN assigned to the public container group."
  value       = azurerm_container_group.app.fqdn
}

output "app_ip_address" {
  description = "Public IP address of the container group."
  value       = azurerm_container_group.app.ip_address
}

output "resource_group_name" {
  description = "Name of the resource group (for teardown reference)."
  value       = azurerm_resource_group.main.name
}

output "table_endpoint" {
  description = "Non-secret HTTPS endpoint used for persistent inventory."
  value       = azurerm_storage_account.inventory.primary_table_endpoint
}

output "table_name" {
  value = azapi_resource.inventory_table.name
}
