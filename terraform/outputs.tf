# ──────────────────────────────────────────────────────────────
# Outputs – used by CI/CD for smoke tests
# ──────────────────────────────────────────────────────────────

output "app_url" {
  description = "Public URL of the deployed API (http://<fqdn>:<port>)."
  value       = "http://${azurerm_container_group.app.fqdn}:${var.container_port}"
}

output "app_fqdn" {
  description = "FQDN assigned by Azure to the container group."
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
