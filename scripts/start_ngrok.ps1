# scripts/start_ngrok.ps1
# PowerShell script to start ngrok tunnel for webhook development

param(
    [int]$Port = 8000,
    [string]$Region = "us",
    [switch]$Help
)

if ($Help) {
    Write-Host "Ngrok Tunnel Starter for Facebook/TikTok Webhooks" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\start_ngrok.ps1 [-Port <port>] [-Region <region>]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Port      Port to expose (default: 8000)"
    Write-Host "  -Region    ngrok region (us, eu, ap, au, sa, jp, in - default: us)"
    Write-Host "  -Help      Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\start_ngrok.ps1                  # Start with defaults"
    Write-Host "  .\start_ngrok.ps1 -Port 3000       # Expose port 3000"
    Write-Host "  .\start_ngrok.ps1 -Region eu       # Use EU region"
    exit 0
}

# Check if ngrok is installed
Write-Host "Checking for ngrok..." -ForegroundColor Cyan
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue

if (-not $ngrokPath) {
    Write-Host "ERROR: ngrok is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install ngrok:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://ngrok.com/download"
    Write-Host "  2. Or install with Chocolatey: choco install ngrok"
    Write-Host ""
    exit 1
}

Write-Host "✓ ngrok found at: $($ngrokPath.Source)" -ForegroundColor Green

# Check if port is in use
Write-Host "Checking if port $Port is in use..." -ForegroundColor Cyan
$portInUse = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue

if (-not $portInUse) {
    Write-Host "WARNING: Port $Port is not in use. Make sure your app is running!" -ForegroundColor Yellow
    Write-Host "Start your app first with: uvicorn app.main:app --reload --port $Port" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne 'y') {
        exit 0
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " Starting ngrok tunnel for webhooks..." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Port:   $Port" -ForegroundColor White
Write-Host "Region: $Region" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop the tunnel" -ForegroundColor Yellow
Write-Host ""

# Start ngrok
Write-Host "Launching ngrok..." -ForegroundColor Green
ngrok http $Port --region=$Region

# Note: Script will block here until ngrok is stopped
