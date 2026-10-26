#requires -Version 5.1
[CmdletBinding()]
param([string]$Python = 'python')

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'Continue'
$buildRoot = Join-Path $PSScriptRoot '.build'
$buildTemp = Join-Path $buildRoot 'tmp'
$venvPython = Join-Path $PSScriptRoot '.venv-build\Scripts\python.exe'
$oldTemp = $env:TEMP
$oldTmp = $env:TMP
$oldInstallerCache = $env:PYINSTALLER_CONFIG_DIR

New-Item -ItemType Directory -Path $buildTemp -Force | Out-Null
Push-Location $PSScriptRoot
try {
    $env:TEMP = $buildTemp
    $env:TMP = $buildTemp
    $env:PYINSTALLER_CONFIG_DIR = Join-Path $buildRoot 'cache'

    if (-not (Test-Path -LiteralPath $venvPython)) {
        & $Python -m venv (Join-Path $PSScriptRoot '.venv-build')
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the build environment.' }
    }
    & $venvPython -m pip install --disable-pip-version-check --no-cache-dir -r (Join-Path $PSScriptRoot 'requirements-build.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the build dependencies.' }

    & $venvPython -m unittest discover -s (Join-Path $PSScriptRoot 'tests') -v
    if ($LASTEXITCODE -ne 0) { throw 'Regression tests failed. The executable was not built.' }

    # This environment is already isolated, so PyBuilder needs no extra venvs.
    & (Join-Path $PSScriptRoot '.venv-build\Scripts\pyb.exe') --no-venvs exe
    if ($LASTEXITCODE -ne 0) { throw 'The executable build failed. Read the output above.' }
    Write-Host "Built: $(Join-Path $PSScriptRoot 'dist\WindowsOptimizer.exe')" -ForegroundColor Green
} finally {
    $env:TEMP = $oldTemp
    $env:TMP = $oldTmp
    $env:PYINSTALLER_CONFIG_DIR = $oldInstallerCache
    Pop-Location
}
