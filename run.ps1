# run.ps1 — Build and start the Weather Fusion Simulator, then print the
# dashboard URL right here in PowerShell once it's actually ready.
#
# Usage:
#   .\run.ps1

$ErrorActionPreference = "Stop"

$dashboardUrl = "http://localhost:5000"
$emqxDashboardUrl = "http://localhost:18083"

if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "No .env file found." -ForegroundColor Yellow
    Write-Host "Creating one from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Edit .env now and fill in your real API keys, then run .\run.ps1 again." -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "Building and starting containers (the first run can take a few minutes)..." -ForegroundColor Cyan
Write-Host ""

docker compose up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "docker compose failed to start. See the error above." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Containers started. Waiting for the dashboard to respond..." -ForegroundColor Cyan

$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $response = Invoke-WebRequest -Uri $dashboardUrl -UseBasicParsing -TimeoutSec 2
        if ($response.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Host ""
if ($ready) {
    Write-Host "Dashboard is up and ready." -ForegroundColor Green
} else {
    Write-Host "Containers are running, but the dashboard didn't respond within the timeout." -ForegroundColor Yellow
    Write-Host "Check what's happening with:" -ForegroundColor Yellow
    Write-Host "  docker compose ps" -ForegroundColor Yellow
    Write-Host "  docker compose logs dashboard" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "  Dashboard:       $dashboardUrl" -ForegroundColor Green
Write-Host "  EMQX Dashboard:  $emqxDashboardUrl  (login: admin / public)" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green
Write-Host ""

if ($ready) {
    Start-Process $dashboardUrl
}
