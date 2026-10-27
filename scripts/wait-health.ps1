param([Parameter(Mandatory=$true)][string]$BaseUrl, [int]$Attempts = 30)
$ErrorActionPreference = 'Stop'
for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    try {
        $result = Invoke-RestMethod -Uri "$($BaseUrl.TrimEnd('/'))/health" -TimeoutSec 3
        if ($result.status -eq 'ok') { Write-Output 'Health check passed'; return }
    } catch { Write-Verbose "Waiting for API, attempt $attempt" }
    Start-Sleep -Seconds 2
}
throw "API did not become healthy after $Attempts attempts"
