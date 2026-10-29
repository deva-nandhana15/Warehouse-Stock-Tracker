. "$PSScriptRoot/common.ps1"
$target = Join-Path $PSScriptRoot '../jenkins/assets'
New-Item -ItemType Directory -Force $target | Out-Null
function Get-CheckedArchive {
    param([string]$Base, [string]$Archive, [string]$Checksums)
    Invoke-WebRequest "$Base/$Archive" -OutFile "$target/$Archive" -UseBasicParsing
    Invoke-WebRequest "$Base/$Checksums" -OutFile "$target/$Checksums" -UseBasicParsing
    $line = @(Get-Content "$target/$Checksums" | Where-Object { ($_ -split '\s+')[-1] -eq $Archive })
    if ($line.Count -ne 1) { throw "Missing or ambiguous checksum for $Archive" }
    if ((Get-FileHash "$target/$Archive" -Algorithm SHA256).Hash -ne ($line[0] -split '\s+')[0]) { throw "Checksum mismatch: $Archive" }
    Write-Output "Checksum verified: $Archive"
}
Get-CheckedArchive 'https://releases.hashicorp.com/terraform/1.17.0' 'terraform_1.17.0_linux_amd64.zip' 'terraform_1.17.0_SHA256SUMS'
Get-CheckedArchive 'https://github.com/gitleaks/gitleaks/releases/download/v8.30.1' 'gitleaks_8.30.1_linux_x64.tar.gz' 'gitleaks_8.30.1_checksums.txt'
$archive = 'trivy_0.76.1_Linux-64bit.tar.gz'
$base = 'https://github.com/aquasecurity/trivy/releases/download/v0.76.1'
if (!(Test-Path "$target/$archive")) { Invoke-WebRequest "$base/$archive" -OutFile "$target/$archive" -UseBasicParsing }
if (!(Test-Path "$target/$archive.sigstore.json")) { Invoke-WebRequest "$base/$archive.sigstore.json" -OutFile "$target/$archive.sigstore.json" -UseBasicParsing }
Invoke-Checked "$PSScriptRoot/../.tools/cosign/cosign-windows-amd64.exe" @('verify-blob', "$target/$archive", '--bundle', "$target/$archive.sigstore.json", '--certificate-oidc-issuer', 'https://token.actions.githubusercontent.com', '--certificate-identity', 'https://github.com/aquasecurity/trivy/.github/workflows/reusable-release.yaml@refs/tags/v0.76.1')
$manifest = Get-ChildItem $target -File | Where-Object {$_.Name -match '\.(zip|tar\.gz)$'} | ForEach-Object { (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower() + '  ' + $_.Name }
$manifest | Set-Content "$target/SHA256SUMS" -Encoding ascii

# Resolve and pin required plugin dependencies from the official update center.
$center = Invoke-RestMethod 'https://updates.jenkins.io/current/update-center.actual.json'
$queue = [System.Collections.Generic.Queue[string]]::new()
foreach($name in @('workflow-aggregator','git','credentials-binding','junit')) { $queue.Enqueue($name) }
$selected = @{}
while($queue.Count -gt 0) {
    $name = $queue.Dequeue()
    if ($selected.ContainsKey($name)) { continue }
    $plugin = $center.plugins.$name
    if (!$plugin) { throw "Plugin missing from official update center: $name" }
    if ([version]$plugin.requiredCore -gt [version]'2.580.2') { throw "Plugin $name needs Jenkins $($plugin.requiredCore)" }
    $selected[$name] = $plugin.version
    foreach($dependency in $plugin.dependencies) { if(!$dependency.optional) { $queue.Enqueue($dependency.name) } }
}
$selected.Keys | Sort-Object | ForEach-Object { $_ + ':' + $selected[$_] } | Set-Content "$PSScriptRoot/../jenkins/plugins.txt" -Encoding ascii
Write-Output "Pinned $($selected.Count) required Jenkins plugins"
