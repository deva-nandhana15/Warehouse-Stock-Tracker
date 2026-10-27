param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$ImageTag,
    [string]$StorageAccountName = 'stwhdevanandhana15',
    [string]$DnsLabel = 'warehouse-devanandhana15',
    [string]$Location = 'centralindia',
    [switch]$GrantDeveloperAccess
)
. "$PSScriptRoot/common.ps1"
$subscription = & az account show --query id -o tsv
if ($LASTEXITCODE -ne 0) { throw 'Sign in with az login first' }
$env:TF_VAR_azure_subscription_id = "$subscription".Trim()
$env:TF_VAR_storage_account_name = $StorageAccountName
$env:TF_VAR_dns_label = $DnsLabel
$env:TF_VAR_location = $Location
$env:TF_VAR_container_image = 'dva15/warehouse-stock-tracker'
$env:TF_VAR_container_image_tag = $ImageTag
if ($GrantDeveloperAccess) {
    $userId = & az ad signed-in-user show --query id -o tsv
    if ($LASTEXITCODE -ne 0) { throw 'Could not resolve developer user object ID' }
    $env:TF_VAR_developer_object_id = "$userId".Trim()
}
foreach ($namespace in @('Microsoft.Storage', 'Microsoft.ContainerInstance', 'Microsoft.ManagedIdentity')) {
    $state = & az provider show --namespace $namespace --query registrationState -o tsv
    if ($LASTEXITCODE -ne 0) { throw "Cannot check provider $namespace" }
    if ("$state".Trim() -ne 'Registered') {
        Write-Warning "Owner action required before apply: az provider register --namespace $namespace --wait"
    }
}
Invoke-Checked terraform @('-chdir=terraform', 'fmt', '-check')
Invoke-Checked terraform @('-chdir=terraform', 'init', '-input=false', '-lockfile=readonly')
Invoke-Checked terraform @('-chdir=terraform', 'validate', '-no-color')
Invoke-Checked terraform @('-chdir=terraform', 'plan', '-input=false', '-out=tfplan', '-no-color')
Write-Output 'Plan saved. Review resources and Azure cost before running terraform -chdir=terraform apply tfplan yourself.'
