# Windows 10/11 startup script
# - Creates a venv if missing using the best available Python launcher (py -3 preferred, fallback to python)
# - Does NOT activate the venv (avoids PowerShell ExecutionPolicy issues)
# - Uses the venv's python.exe directly for pip installs and running main.py
# - Installs requirements only if requirements.txt exists and is non-empty

$ErrorActionPreference = "Stop"

# Move to repo root
Set-Location -Path $PSScriptRoot

function Get-BasePython {
  # Prefer the Windows Python launcher 'py -3' when available; fallback to 'python'
  if (Get-Command py -ErrorAction SilentlyContinue) {
    return @('py','-3')
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return @('python')
  }
  throw "No suitable Python found. Install Python 3 from https://www.python.org/downloads/windows/ or the Microsoft Store."
}

$venv = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venv)) {
  $PY = Get-BasePython
  & $PY -m venv $venv
}

# Use the venv's interpreter directly
$venvPy = Join-Path $venv "Scripts/python.exe"
if (-not (Test-Path $venvPy)) {
  throw "Virtual environment appears corrupted or incomplete: $venvPy not found. Try deleting .venv and re-running."
}

# Upgrade pip inside the venv (non-fatal)
& $venvPy -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
  Write-Warning "pip upgrade failed; continuing"
}

# Install dependencies if requirements.txt exists and is non-empty
$req = Join-Path $PSScriptRoot "requirements.txt"
if ((Test-Path $req) -and ((Get-Item $req).Length -gt 0)) {
  # Install requirements (non-fatal)
  & $venvPy -m pip install -r $req
  if ($LASTEXITCODE -ne 0) {
    Write-Warning "requirements install failed; continuing"
  }
} else {
  Write-Host "requirements.txt is empty or missing; skipping install"
}

# Verify Tk availability (tkinter)
& $venvPy -c "import tkinter as _tk" *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Error "Tkinter (Tk) is not available in this Python environment."
  Write-Host "Install Python 3 with Tk support, then delete .venv and re-run this script. Options:" -ForegroundColor Yellow
  Write-Host "  - Install from Microsoft Store: 'Python 3.x'" -ForegroundColor Yellow
  Write-Host "  - Or download from https://www.python.org/downloads/windows/" -ForegroundColor Yellow
  exit 1
}

# Run the app using the venv's Python
& $venvPy (Join-Path $PSScriptRoot "main.py")
