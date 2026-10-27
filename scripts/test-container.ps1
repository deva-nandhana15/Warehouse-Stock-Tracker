param([Parameter(Mandatory=$true)][string]$Image)
. "$PSScriptRoot/common.ps1"
$containerId = $null
try {
    $containerId = & docker run -d --rm -p '127.0.0.1::5000' -e APP_VERSION=ci $Image
    if ($LASTEXITCODE -ne 0) { throw 'Container startup failed' }
    $containerId = "$containerId".Trim()
    $mapping = & docker port $containerId 5000/tcp
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read mapped port' }
    $port = ("$mapping".Trim() -split ':')[-1]
    $baseUrl = "http://127.0.0.1:$port"
    & "$PSScriptRoot/wait-health.ps1" -BaseUrl $baseUrl
    $page = Invoke-WebRequest -Uri $baseUrl -Headers @{Accept='text/html'} -UseBasicParsing
    if ($page.Content -notmatch 'id="inventory-body"') { throw 'Dashboard is missing from the container' }
    foreach ($asset in @('/static/styles.css', '/static/app.js')) {
        $null = Invoke-WebRequest -Uri "$baseUrl$asset" -UseBasicParsing
    }
    $uid = & docker exec $containerId id -u
    if ($LASTEXITCODE -ne 0 -or "$uid".Trim() -ne '10001') { throw 'Expected UID 10001' }
    Invoke-Checked -File "$PSScriptRoot/../node_modules/.bin/newman.cmd" -Arguments @('run', 'postman/collection.json', '--env-var', "baseUrl=$baseUrl", '--reporters', 'cli,junit', '--reporter-junit-export', 'reports/newman.xml')
} finally {
    if ($containerId) { Invoke-Checked -File docker -Arguments @('stop', $containerId) }
}
