# WSL Port Forwarding Setup - Permanent localhost Solution
# Run this as Administrator once to enable localhost access to WSL services
# This makes WSL services accessible at localhost:8000 and localhost:3000 from Windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "WSL Port Forwarding Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get WSL IP address
Write-Host "[1/3] Getting WSL IP address..." -ForegroundColor Yellow
$wslIp = (wsl hostname -I).Trim()
Write-Host "   WSL IP: $wslIp" -ForegroundColor Green

# Remove existing port forwarding rules if any
Write-Host ""
Write-Host "[2/3] Removing old port forwarding rules..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null
Write-Host "   Done" -ForegroundColor Green

# Add new port forwarding rules
Write-Host ""
Write-Host "[3/3] Adding port forwarding rules..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIp
Write-Host "   Port 8000 (backend) -> WSL" -ForegroundColor Green
Write-Host "   Port 3000 (frontend) -> WSL" -ForegroundColor Green

# Show current rules
Write-Host ""
Write-Host "Current port forwarding rules:" -ForegroundColor Cyan
netsh interface portproxy show v4tov4

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now access your services at:" -ForegroundColor Yellow
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: Run this script again after restarting Windows" -ForegroundColor Yellow
Write-Host "      (WSL IP may change and forwarding rules need updating)" -ForegroundColor Yellow
Write-Host ""
