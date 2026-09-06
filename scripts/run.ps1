#Requires -Version 5.1
<#
.SYNOPSIS
    Single-command entry point for the 3D localization benchmark (Windows).

.DESCRIPTION
    This is the Windows PowerShell equivalent of scripts/run.sh. It:
      1. creates/reuses a local virtual environment and installs dependencies
      2. runs the full test suite
      3. validates the experiment configuration
      4. runs the smoke benchmark, then the standard benchmark
      5. writes all result tables and builds the Excel workbook
      6. validates the generated outputs
      7. prints the output locations

    It does not exit or close the calling shell, so your PowerShell session
    stays open after it finishes.

.PARAMETER SmokeOnly
    Run only the smoke benchmark (fast); skip the 96-scenario standard sweep.

.PARAMETER SkipTests
    Skip the pytest run (not recommended).

.EXAMPLE
    .\scripts\run.ps1

.EXAMPLE
    .\scripts\run.ps1 -SmokeOnly

.NOTES
    Requires Python 3.10+ on PATH as either `py` (the Windows launcher) or
    `python`. If PowerShell blocks running this script, either run it from
    an elevated prompt with:
        powershell -ExecutionPolicy Bypass -File scripts\run.ps1
    or allow local scripts once with:
        Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
#>
[CmdletBinding()]
param(
    [switch]$SmokeOnly,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @{ Exe = "py"; BaseArgs = @("-3") }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @{ Exe = "python"; BaseArgs = @() }
    }
    throw "No Python interpreter found on PATH (tried 'py' and 'python'). Install Python 3.10+ from https://www.python.org/downloads/windows/ and ensure 'Add python.exe to PATH' is checked during setup."
}

function Invoke-Python {
    param([string[]]$CommandArgs)
    & $script:PythonExe @($script:PythonBaseArgs + $CommandArgs)
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed (exit code $LASTEXITCODE): $($script:PythonExe) $($CommandArgs -join ' ')"
    }
}

$pythonCmd = Get-PythonCommand
$script:PythonExe = $pythonCmd.Exe
$script:PythonBaseArgs = $pythonCmd.BaseArgs

Write-Host "=== [1/7] Preparing runtime ===" -ForegroundColor Cyan
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment at $VenvDir"
    Invoke-Python @("-m", "venv", $VenvDir)
}

if (-not (Test-Path $VenvPython)) {
    throw "Virtual environment python.exe not found at $VenvPython. Delete $VenvDir and re-run this script."
}

& $VenvPython -m pip install --quiet --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
& $VenvPython -m pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "dependency installation failed" }

if (-not $SkipTests) {
    Write-Host ""
    Write-Host "=== [2/7] Running the test suite ===" -ForegroundColor Cyan
    & $VenvPython -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "test suite failed" }
} else {
    Write-Host ""
    Write-Host "=== [2/7] Skipping test suite (-SkipTests) ===" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== [3/7] Validating experiment configuration ===" -ForegroundColor Cyan
& $VenvPython -m locbench3d.cli validate-config (Join-Path "examples" "experiment_smoke.yaml")
if ($LASTEXITCODE -ne 0) { throw "smoke config validation failed" }
if (-not $SmokeOnly) {
    & $VenvPython -m locbench3d.cli validate-config (Join-Path "examples" "experiment_standard.yaml")
    if ($LASTEXITCODE -ne 0) { throw "standard config validation failed" }
}

Write-Host ""
Write-Host "=== [4/7] Running the smoke benchmark ===" -ForegroundColor Cyan
& $VenvPython -m locbench3d.cli run-all --smoke --out (Join-Path "output" "smoke")
if ($LASTEXITCODE -ne 0) { throw "smoke benchmark failed" }

if (-not $SmokeOnly) {
    Write-Host ""
    Write-Host "=== [5/7] Running the standard benchmark ===" -ForegroundColor Cyan
    & $VenvPython -m locbench3d.cli run-all --config (Join-Path "examples" "experiment_standard.yaml") --out (Join-Path "output" "standard")
    if ($LASTEXITCODE -ne 0) { throw "standard benchmark failed" }
} else {
    Write-Host ""
    Write-Host "=== [5/7] Skipping standard benchmark (-SmokeOnly) ===" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== [6/7] Result tables and workbook already validated by run-all ===" -ForegroundColor Cyan

Write-Host ""
Write-Host "=== [7/7] Output locations ===" -ForegroundColor Cyan
Write-Host "  Smoke run tables:    $ProjectRoot\output\smoke\tables\"
Write-Host "  Smoke run workbook:  $ProjectRoot\output\smoke\workbook.xlsx"
if (-not $SmokeOnly) {
    Write-Host "  Standard run tables:   $ProjectRoot\output\standard\tables\"
    Write-Host "  Standard run workbook: $ProjectRoot\output\standard\workbook.xlsx"
}
Write-Host ""
Write-Host "Done. This shell is still yours." -ForegroundColor Green
Write-Host "The virtual environment used here lives at $VenvDir."
Write-Host "To use it directly in this shell, run: $VenvDir\Scripts\Activate.ps1"
