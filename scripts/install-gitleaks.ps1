. "$PSScriptRoot/common.ps1"
$version = '8.30.1'
$asset = "gitleaks_${version}_windows_x64.zip"
$target = Join-Path $PSScriptRoot '../.tools/gitleaks'
New-Item -ItemType Directory -Force -Path $target | Out-Null
$base = "https://github.com/gitleaks/gitleaks/releases/download/v$version"
Invoke-WebRequest "$base/$asset" -OutFile "$target/$asset" -UseBasicParsing
Invoke-WebRequest "$base/gitleaks_${version}_checksums.txt" -OutFile "$target/checksums.txt" -UseBasicParsing
$line = @(Get-Content "$target/checksums.txt" | Where-Object { ($_ -split '\s+')[-1] -eq $asset })
if ($line.Count -ne 1) { throw 'Expected exactly one matching checksum' }
$expected = ($line[0] -split '\s+')[0]
if ((Get-FileHash "$target/$asset" -Algorithm SHA256).Hash -ne $expected) { throw 'Checksum mismatch' }
Expand-Archive -LiteralPath "$target/$asset" -DestinationPath $target -Force
Invoke-Checked -File "$target/gitleaks.exe" -Arguments @('version')
