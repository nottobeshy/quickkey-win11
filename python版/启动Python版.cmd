@echo off
setlocal
cd /d "%~dp0"

set "BUNDLED=C:\Users\Tx\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if exist "%BUNDLED%" (
  start "" "%BUNDLED%" "%~dp0quickkey.pyw"
  exit /b 0
)

where pyw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pyw.exe -3 "%~dp0quickkey.pyw"
  exit /b 0
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pythonw.exe "%~dp0quickkey.pyw"
  exit /b 0
)

powershell.exe -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Python 3 was not found. Install Python 3 with tkinter, then run this launcher again.','QuickKey Python')"
exit /b 1

