@echo off
chcp 65001 >nul
title Project Launcher
echo ========================================
echo    Project Launcher - Windows
echo ========================================
echo.
echo 正在启动...
cd /d "%~dp0"
python server.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 未找到 Python，请安装 Python 3
    echo    https://www.python.org/downloads/
    echo.
    pause
)
