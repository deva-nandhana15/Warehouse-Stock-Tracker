. "$PSScriptRoot/common.ps1"
# Independent bootstrap: the official Python Sigstore verifier, installed from
# PyPI, authenticates the Cosign bundle before the executable is ever run.
$target = Join-Path $PSScriptRoot '../.tools/cosign'
$python = Join-Path $PSScriptRoot '../.tools/verify/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python)) {
    Invoke-Checked python @('-m', 'venv', "$PSScriptRoot/../.tools/verify")
}
Invoke-Checked $python @('-m', 'pip', 'install', 'sigstore==4.5.1')
New-Item -ItemType Directory -Force $target | Out-Null
$base = 'https://github.com/sigstore/cosign/releases/download/v3.1.4'
$file = 'cosign-windows-amd64.exe'
Invoke-WebRequest "$base/$file" -OutFile "$target/$file" -UseBasicParsing
Invoke-WebRequest "$base/$file.sigstore.json" -OutFile "$target/$file.sigstore.json" -UseBasicParsing
Invoke-Checked $python @('-m', 'sigstore', 'verify', 'identity', '--bundle', "$target/$file.sigstore.json", '--cert-identity', 'keyless@projectsigstore.iam.gserviceaccount.com', '--cert-oidc-issuer', 'https://accounts.google.com', "$target/$file")
Invoke-Checked "$target/$file" @('version')
