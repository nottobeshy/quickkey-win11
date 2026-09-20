@echo off
setlocal
set "APP="
for /r "%~dp0" %%F in (quickkey.pyw) do set "APP=%%F"
if not defined APP exit /b 1

set "BUNDLED=C:\Users\Tx\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if exist "%BUNDLED%" (
  start "" "%BUNDLED%" "%APP%"
  exit /b 0
)

where pyw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pyw.exe -3 "%APP%"
  exit /b 0
)

where pythonw.exe >nul 2>nul
if not errorlevel 1 (
  start "" pythonw.exe "%APP%"
  exit /b 0
)

powershell.exe -NoProfile -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Python 3 was not found. Install Python 3 with tkinter, then run this launcher again.','QuickKey Python')"
exit /b 1

