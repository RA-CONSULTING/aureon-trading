Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "`n🐙 AUREON UNIFIED ECOSYSTEM (Windows)" -ForegroundColor Cyan
Write-Host "This bootstraps deps + runs LIVE_NOW.py (Mycelium/Unified Ecosystem).`n" -ForegroundColor Cyan

if (-not (Test-Path -Path ".venv")) {
  Write-Host "Creating venv..." -ForegroundColor Yellow
  py -3 -m venv .venv
}

Write-Host "Activating venv..." -ForegroundColor Yellow
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host "Installing requirements..." -ForegroundColor Yellow
python -m pip install -r requirements.txt

Write-Host "Running LIVE_NOW.py..." -ForegroundColor Green
python LIVE_NOW.py
