param([Parameter(Mandatory=$true)][string]$BaseUrl, [int]$Attempts = 90)
$ErrorActionPreference = 'Stop'
for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
    try {
        $result = Invoke-RestMethod -Uri "$($BaseUrl.TrimEnd('/'))/ready" -TimeoutSec 15
        if ($result.status -eq 'ready' -and $result.storage -eq 'azure-table') {
            Write-Output 'Azure application and persistent inventory storage are ready'
            return
        }
    } catch { Write-Verbose "Waiting for storage access, attempt $attempt" }
    Start-Sleep -Seconds 2
}
throw 'Azure storage readiness failed. Check the table, managed identity role and RBAC propagation.'
