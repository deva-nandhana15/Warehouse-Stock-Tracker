# Approved security-policy exception

Approved by the project owner in this chat on 2026-10-27.

| Field | Decision |
|---|---|
| Rule | Trivy AZU-0012: default-deny storage network rules |
| Scope | Only terraform/storage.tf, the project inventory storage account |
| Reason | Keep the classroom deployment to public ACI plus Azure Table Storage, without gateway/NAT/VNet overhead |
| Controls retained | HTTPS/TLS 1.2+, table-scoped managed identity, shared-key authentication disabled, anonymous blob access disabled |
| Accepted residual risk | Storage endpoint remains publicly reachable; authorized data operations still require identity permissions |
| Use restriction | Synthetic course-project data only |
| Expiry | 2026-11-26; renew explicitly or implement restricted networking |

The pipeline passes `.trivyignore.yaml` explicitly only to the configuration
scanner. The exception does not apply to secrets, Python code, dependency or image
vulnerabilities, other infrastructure checks, or unrelated Terraform files. All
non-excepted HIGH/CRITICAL configuration findings retain exit code 1.

Trivy reports paths relative to its scan root, so the YAML path is `storage.tf`.
The pipeline fixes that root to `terraform`; do not reuse this ignore file against
an unrelated directory. An additional temporary scope-probe command was declined
and was not executed; no broader scope-testing result is claimed.

This records an accepted risk, not a claim that the network restriction exists.
No Azure deployment has been performed by approving this exception.
