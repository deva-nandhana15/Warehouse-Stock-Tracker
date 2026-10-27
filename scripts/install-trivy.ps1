param([Parameter(Mandatory=$true)][string]$CosignPath)
. "$PSScriptRoot/common.ps1"
# Bootstrap cosign independently using the official Sigstore verification procedure.
# No bypass: the downloaded archive is extracted only after signature verification.
$version = '0.76.1'
$tag = "v$version"
$asset = "trivy_${version}_windows-64bit.zip"
$target = Join-Path $PSScriptRoot '../.tools/trivy'
New-Item -ItemType Directory -Force -Path $target | Out-Null
$base = "https://github.com/aquasecurity/trivy/releases/download/$tag"
Invoke-WebRequest "$base/$asset" -OutFile "$target/$asset" -UseBasicParsing
Invoke-WebRequest "$base/$asset.sigstore.json" -OutFile "$target/$asset.sigstore.json" -UseBasicParsing
Invoke-Checked -File $CosignPath -Arguments @('verify-blob', "$target/$asset", '--bundle', "$target/$asset.sigstore.json", '--certificate-oidc-issuer', 'https://token.actions.githubusercontent.com', '--certificate-identity', "https://github.com/aquasecurity/trivy/.github/workflows/reusable-release.yaml@refs/tags/$tag")
Expand-Archive -LiteralPath "$target/$asset" -DestinationPath $target -Force
Invoke-Checked -File "$target/trivy.exe" -Arguments @('--version')
