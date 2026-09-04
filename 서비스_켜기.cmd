@echo off
chcp 65001 >nul
title AI Solverthon - Start Service
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0server\.deploy\start-service.ps1"
echo.
if errorlevel 1 (
  echo Failed to start the service. Check the error above.
) else (
  echo The service is running normally.
)
pause
