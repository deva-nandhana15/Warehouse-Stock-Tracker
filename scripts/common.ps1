Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Windows PowerShell does not throw when a native executable exits nonzero.
function Invoke-Checked {
    param([Parameter(Mandatory=$true)][string]$File, [string[]]$Arguments = @())
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$File failed with exit code $LASTEXITCODE" }
}
