@echo off
chcp 65001 >nul
title AI Solverthon - Stop Service
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0server\.deploy\stop-service.ps1"
echo.
if errorlevel 1 (
  echo Failed to stop the service. Check the error above.
) else (
  echo The service was stopped normally.
)
pause
