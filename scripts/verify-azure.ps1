param(
    [string]$BaseUrl,
    [string]$ExpectedVersion,
    [switch]$TestPersistence
)
. "$PSScriptRoot/common.ps1"
if (!$BaseUrl) {
    $BaseUrl = & terraform -chdir=terraform output -raw app_url
    if ($LASTEXITCODE -ne 0) { throw 'Cannot resolve deployed application URL' }
    $BaseUrl = "$BaseUrl".Trim()
}
& "$PSScriptRoot/wait-health.ps1" -BaseUrl $BaseUrl
& "$PSScriptRoot/wait-ready.ps1" -BaseUrl $BaseUrl
$metadata = Invoke-RestMethod "$BaseUrl/api" -TimeoutSec 15
if ($ExpectedVersion -and $metadata.version -ne $ExpectedVersion) { throw 'Azure is not running the expected release' }
$storage = Invoke-RestMethod "$BaseUrl/storage" -TimeoutSec 15
if ($storage.backend -ne 'azure-table' -or !$storage.persistent) { throw 'Cloud persistence is not configured' }
$page = Invoke-WebRequest $BaseUrl -Headers @{Accept='text/html'} -UseBasicParsing -TimeoutSec 15
if ($page.Content -notmatch 'id="inventory-body"') { throw 'Dashboard is missing' }
$evidence = [ordered]@{
    checked_at = [DateTimeOffset]::UtcNow.ToString('o')
    app_url = $BaseUrl
    version = $metadata.version
    storage = $storage.backend
    health = 'passed'
    readiness = 'passed'
    dashboard = 'passed'
    persistence_after_restart = 'not tested'
}
if ($TestPersistence) {
    # Explicit opt-in: adds one clearly synthetic item and restarts only this app.
    $sku = 'VERIFY-' + [guid]::NewGuid().ToString('N').Substring(0, 12)
    $body = @{sku=$sku; name='Persistence verification (synthetic)'; quantity=7; reorder_level=2} | ConvertTo-Json
    $item = Invoke-RestMethod "$BaseUrl/items" -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 15
    if ($item.quantity -ne 7) { throw 'Verification item was not created correctly' }
    Invoke-Checked az @('container', 'restart', '--resource-group', 'rg-warehouse-stock-tracker', '--name', 'ci-warehouse-stock-tracker', '--output', 'none')
    & "$PSScriptRoot/wait-ready.ps1" -BaseUrl $BaseUrl
    $items = @(Invoke-RestMethod "$BaseUrl/items" -TimeoutSec 15)
    $saved = @($items | Where-Object {$_.sku -eq $sku})
    if ($saved.Count -ne 1 -or $saved[0].quantity -ne 7) { throw 'Inventory did not survive the container restart' }
    $evidence.persistence_after_restart = 'passed'
    $evidence.verification_sku = $sku
}
New-Item -ItemType Directory -Force reports | Out-Null
$evidence | ConvertTo-Json | Set-Content reports/azure-live-verification.json -Encoding utf8
$evidence | Format-List
