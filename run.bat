@echo off
chcp 65001 >nul
title HR 工具箱 - 运行日志
echo ========================================
echo   HR 工具箱 启动中...
echo ========================================
echo.

cd /d "%~dp0"

.venv\Scripts\python.exe -m app.main

pause
