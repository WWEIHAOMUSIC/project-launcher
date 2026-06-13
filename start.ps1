# Project Launcher - Windows (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Project Launcher - Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$port = 9876
$inUse = netstat -ano | Select-String ":$port"
if ($inUse) {
    Write-Host "⚠️  Port $port is in use. Trying to close existing process..." -ForegroundColor Yellow
    $pid = ($inUse | Select-Object -First 1) -replace '.*\s+(\d+)$', '$1'
    if ($pid -match '^\d+$') {
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

Write-Host "Starting Project Launcher..." -ForegroundColor Green
python "$PSScriptRoot\server.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Python not found. Please install Python 3:" -ForegroundColor Red
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
}
