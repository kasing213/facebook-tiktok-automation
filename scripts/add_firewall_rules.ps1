# Add Windows Firewall Rules for WSL Services
# Run as Administrator to allow localhost access to WSL backend

Write-Host "Adding Windows Firewall rules for WSL services..." -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

# Remove existing rules if they exist
Write-Host "[1/2] Removing old firewall rules (if any)..." -ForegroundColor Yellow
Remove-NetFirewallRule -DisplayName "WSL Backend Port 8000" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "WSL Frontend Port 3000" -ErrorAction SilentlyContinue
Write-Host "   Done" -ForegroundColor Green

# Add new rules
Write-Host ""
Write-Host "[2/2] Adding new firewall rules..." -ForegroundColor Yellow

New-NetFirewallRule -DisplayName "WSL Backend Port 8000" `
    -Direction Inbound `
    -LocalPort 8000 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any | Out-Null
Write-Host "   Added rule for port 8000 (Backend)" -ForegroundColor Green

New-NetFirewallRule -DisplayName "WSL Frontend Port 3000" `
    -Direction Inbound `
    -LocalPort 3000 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any | Out-Null
Write-Host "   Added rule for port 3000 (Frontend)" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Firewall Rules Added Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now access:" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
