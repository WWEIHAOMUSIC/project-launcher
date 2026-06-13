# Project Launcher - Windows (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Project Launcher - Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$port = 9876
$inUse = netstat -ano | Select-String ":$port"
if ($inUse) {
    Write-Host "⚠️  端口 $port 被占用，尝试关闭已有进程..." -ForegroundColor Yellow
    $pidToKill = ($inUse | Select-Object -First 1) -replace '.*\s+(\d+)$', '$1'
    if ($pidToKill -match '^\d+$') {
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
}

Write-Host "🚀 启动 Project Launcher..." -ForegroundColor Green
python "$PSScriptRoot\server.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 未找到 Python，请安装 Python 3" -ForegroundColor Red
    Write-Host "   https://www.python.org/downloads/" -ForegroundColor Gray
    Write-Host ""
    Read-Host "按 Enter 退出"
}
