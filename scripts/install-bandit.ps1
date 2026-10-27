. "$PSScriptRoot/common.ps1"
Invoke-Checked -File "$PSScriptRoot/../.venv/Scripts/python.exe" -Arguments @('-m', 'pip', 'install', '-r', "$PSScriptRoot/../requirements-security.txt")
