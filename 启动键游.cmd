@echo off
cd /d "%~dp0"
if not exist "QuickKey.exe" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"
)
start "" "%~dp0QuickKey.exe"

