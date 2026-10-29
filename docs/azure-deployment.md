# Azure deployment with persistent inventory

**Simple deployment selected; network exception approved 2026-10-27.** The owner chose
public ACI plus authenticated Azure Table Storage, without gateway, NAT or virtual
network additions. The accepted risk is documented in security-exceptions.md and
enforced by the scoped `.trivyignore.yaml`, expiring 2026-11-26. Other security
findings still block. Local tests and security scans pass; Azure deployment and
Jenkins execution still need real evidence.

**Live deployment verified 2026-10-29:** the owner subsequently authorized CLI
creation, and the application is running at
http://warehouse-devanandhana15.centralindia.azurecontainer.io:5000 . Health,
table readiness, expected release and persistence after an actual container
restart passed. Jenkins execution is the remaining CI/CD verification task.

The application runs in Azure Container Instances (ACI). Inventory is stored in
Azure Table Storage and survives app restarts and image redeployments. Terraform
defines both, a user-assigned managed identity, and table-scoped data permissions.
Azure mode starts with an empty inventory and never resets or reseeds cloud data.

The inventory table is provisioned through the Azure management API using pinned
AzAPI provider 2.13.0. AzureRM 5.10.0 manages the other resources. This avoids the
AzureRM table resource's shared-key authentication path while retaining disabled
shared-key access on the storage account. No extra Azure services are required.

## Owner prerequisites

Sign into the intended subscription using `az login`. Confirm it is enabled. The
deployment identity needs permissions to create the resource group, container,
storage account, managed identity and role assignment (for example Owner, or
Contributor plus a suitable role-assignment administration role).

Run required provider registrations in your own terminal; these enable services
for the subscription and do not create the application's resources:

```powershell
az provider register --namespace Microsoft.Storage --wait
az provider register --namespace Microsoft.ContainerInstance --wait
az provider register --namespace Microsoft.ManagedIdentity --wait
```

Terraform automatic provider registration is disabled so the planning step does
not silently perform subscription changes. The selected region must be allowed
by your subscription's policies and have ACI quota.

## Build, test and publish

Use the Git commit SHA of the storage-enabled release, not an earlier UI-only
image. The Jenkins pipeline includes unit/security checks, container tests and
an Azurite persistence/concurrency integration test. Publishing uses the public
Docker Hub repository `dva15/warehouse-stock-tracker` with a full-SHA tag.
Local equivalent commands are in runbook.md; record scanner results before release.

## Plan, review and deploy

Current Central India public retail compute rates retrieved on 2026-10-27 are
USD 0.0426 per vCPU-hour and USD 0.00466 per GB-hour. At the configured 1 vCPU / 1 GB,
compute is approximately USD 0.04726/hour, USD 1.13/day, or USD 34.50 for 730 hours.
Storage capacity, storage transactions, data transfer and applicable taxes are
additional. Student credits may offset charges but are not assumed. No gateway,
NAT gateway or VNet charges are part of this design. Verify subscription-specific
pricing and remaining credit before apply; these are estimates, not spending caps.

Source: https://prices.azure.com/api/retail/prices (Container Instances, Standard,
Central India, consumption meters). Raw retrieved rates are in the ignored
reports/azure-retail-prices.json file.

Run from the project root, replacing the image SHA with the tested published tag:

```powershell
./scripts/plan-azure.ps1 -ImageTag '<FULL_40_CHARACTER_COMMIT_SHA>'
```

Defaults: storage `stwhdevanandhana15`, DNS label `warehouse-devanandhana15`, region
`centralindia`. Override with `-StorageAccountName`, `-DnsLabel`, or `-Location`
if unavailable. Add `-GrantDeveloperAccess` only if the signed-in developer should
also have data access for local testing; this adds a separate table-scoped role.
The helper gets the subscription through Azure CLI and uses process environment
variables. It never writes credentials or real tfvars. It saves `terraform/tfplan`.

Read the proposed changes and current pricing for ACI CPU/memory plus Storage
capacity/transactions. Charges start after creation. Then run yourself:

```powershell
terraform -chdir=terraform apply tfplan
$appUrl = terraform -chdir=terraform output -raw app_url
./scripts/wait-health.ps1 -BaseUrl $appUrl
./scripts/wait-ready.ps1 -BaseUrl $appUrl
Invoke-RestMethod "$appUrl/api"
Start-Process $appUrl
```

The browser shows the dashboard. `/storage` should return `azure-table` and
`persistent: true`; `/ready` checks actual table access. `/health` remains an
independent process-liveness check. Role assignments can take time to propagate;
if readiness initially returns 503, wait and retry before changing credentials.

## Prove persistence

The repeatable helper is `./scripts/verify-azure.ps1`. Its default mode only reads
health, storage, release metadata and the dashboard. Use `-TestPersistence` only
when a synthetic item and one container restart are intended; results are saved
to reports/azure-live-verification.json. Optionally pass `-ExpectedVersion`.

Add an item through the Azure dashboard, record its SKU and quantity, and restart
the ACI group yourself via the Azure portal. Wait for `/ready`, refresh the page,
and confirm the same record exists. Do not run destructive test fixtures against
real inventory; the local persistence test uses only a disposable Azurite container.

## Optional local app with Azure storage

Only after the developer table role has been granted:

```powershell
$env:STORAGE_BACKEND = 'azure-table'
$env:AZURE_AUTH_MODE = 'azure-cli'
$env:AZURE_TABLE_ENDPOINT = terraform -chdir=terraform output -raw table_endpoint
$env:AZURE_TABLE_NAME = 'inventory'
./.venv/Scripts/python.exe app/app.py
```

No storage keys or connection strings are required. Remove those environment
variables to return to local in-memory mode. In ACI, Terraform configures managed
identity authentication instead of CLI authentication.

## Data safety and limitations

ETag-based conditional updates prevent lost concurrent changes and stock going
negative. Conflicts are bounded/retried, then returned as 409. An ambiguous network
failure returns 503; check the current quantity before retrying a stock operation.
The API does not yet offer idempotency keys or an audit ledger.

Storage and table resources have `prevent_destroy` protection. Image replacement
does not delete inventory. A full `terraform destroy` intentionally fails while
these protections remain. For final teardown, back up needed data, explicitly
decide to delete it, remove the two storage protections, review a destroy plan and
run destroy yourself. Do not remove protection as part of routine deploy/rollback.

The table uses an authenticated public HTTPS endpoint, TLS >=1.2, no shared-key
authorization, and no anonymous blob access. The public ACI application still has
no user authentication or TLS front end; use synthetic classroom data. Private
storage networking and authenticated HTTPS app hosting require further infrastructure.

## Official references

- https://learn.microsoft.com/en-us/azure/storage/tables/authorize-access-azure-active-directory
- https://learn.microsoft.com/en-us/azure/container-instances/container-instances-managed-identity
- https://learn.microsoft.com/en-us/python/api/azure-data-tables/azure.data.tables.tableclient
- https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azurite
- https://azure.microsoft.com/pricing/details/container-instances/
- https://azure.microsoft.com/pricing/details/storage/tables/
