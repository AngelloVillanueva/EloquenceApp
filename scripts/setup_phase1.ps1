# PowerShell setup for Phase 1 (RTX 3060 + Python 3.12)
# Usage:  .\scripts\setup_phase1.ps1

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "==> Checking Python 3.12..." -ForegroundColor Cyan
py -3.12 --version

if (-not (Test-Path ".venv")) {
    Write-Host "==> Creating .venv..." -ForegroundColor Cyan
    py -3.12 -m venv .venv
}

Write-Host "==> Activating .venv..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

Write-Host "==> Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip

Write-Host "==> Installing requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "==> Installing PyTorch CUDA 12.4..." -ForegroundColor Cyan
pip install torch --index-url https://download.pytorch.org/whl/cu124

Write-Host "==> Switching to onnxruntime-gpu 1.20.2 (CUDA 12.x)..." -ForegroundColor Cyan
pip uninstall -y onnxruntime onnxruntime-gpu 2>$null
pip install "onnxruntime-gpu==1.20.2"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "==> Created .env from .env.example" -ForegroundColor Green
}

Write-Host "==> Downloading TTS models..." -ForegroundColor Cyan
python scripts/download_models.py

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "1) Install/start Ollama: https://ollama.com/download"
Write-Host "2) ollama pull llama3.1:8b"
Write-Host "3) python scripts/test_inference_pipeline.py"
