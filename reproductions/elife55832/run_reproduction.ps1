param(
    [string]$PythonExe = 'C:\Users\xczhang\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) {
    throw ('Python executable not found: ' + $PythonExe)
}

& $PythonExe (Join-Path $PSScriptRoot 'reproduce_appendix2.py') --output (Join-Path $PSScriptRoot 'outputs')
if ($LASTEXITCODE -ne 0) {
    throw 'Appendix 2 reproduction failed.'
}

& $PythonExe (Join-Path $PSScriptRoot 'reproduce_e27_sequence.py') --data (Join-Path $PSScriptRoot 'data\E27_SAM7') --output (Join-Path $PSScriptRoot 'outputs')
if ($LASTEXITCODE -ne 0) {
    throw 'E27/SAM7 image reproduction failed.'
}

& $PythonExe (Join-Path $PSScriptRoot 'verify_reproduction.py')
if ($LASTEXITCODE -ne 0) {
    throw 'Reproduction verification failed.'
}

Write-Host 'All available reproduction checks passed.'
