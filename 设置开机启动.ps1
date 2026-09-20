$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$exe = Join-Path $root 'QuickKey.exe'
if (-not (Test-Path $exe)) {
    & (Join-Path $root 'build.ps1')
}

$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'QuickKey.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exe
$shortcut.WorkingDirectory = $root
$shortcut.Description = 'QuickKey - Windows 11 shortcut trainer'
$shortcut.Save()

Write-Host "QuickKey was added to Startup: $shortcutPath" -ForegroundColor Green
