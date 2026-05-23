# Установка зависимостей для локальной разработки (Windows)
# Запуск: powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Python:" -ForegroundColor Cyan
python --version

Write-Host "Updating pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "Installing dependencies (may take a few minutes)..." -ForegroundColor Cyan
python -m pip install -r requirements-dev.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "If installation fails on pillow: install Python 3.12 from python.org" -ForegroundColor Yellow
    Write-Host "or run: python -m pip install pillow>=11.0.0" -ForegroundColor Yellow
    exit 1
}

Write-Host "Done. Run unit tests:" -ForegroundColor Green
Write-Host "  pytest tests/ -m `"not integration`"" -ForegroundColor White