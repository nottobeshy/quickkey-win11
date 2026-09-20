param(
    [switch]$Run
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$csc = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$framework = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319'
$wpf = Join-Path $framework 'WPF'
$source = Join-Path $root 'src\QuickKey.cs'
$output = Join-Path $root 'QuickKey.exe'
$manifest = Join-Path $root 'src\app.manifest'
$catalog = Join-Path $root 'data\windows_shortcuts.tsv'

if (-not (Test-Path $csc)) {
    throw 'The built-in .NET Framework C# compiler was not found.'
}
if (-not (Test-Path $catalog)) {
    throw 'The Windows shortcut catalog is missing: data\windows_shortcuts.tsv'
}
$catalogRows = (Get-Content -Encoding UTF8 $catalog | Measure-Object).Count - 1
if ($catalogRows -lt 228) {
    throw "The Windows shortcut catalog is incomplete: $catalogRows rows"
}

$compilerArgs = @(
    '/nologo',
    '/target:winexe',
    '/platform:anycpu',
    '/optimize+',
    '/codepage:65001',
    ('/out:' + $output),
    ('/win32manifest:' + $manifest),
    ('/r:' + (Join-Path $wpf 'PresentationFramework.dll')),
    ('/r:' + (Join-Path $wpf 'PresentationCore.dll')),
    ('/r:' + (Join-Path $wpf 'WindowsBase.dll')),
    ('/r:' + (Join-Path $framework 'System.Xaml.dll')),
    $source
)

& $csc $compilerArgs
if ($LASTEXITCODE -ne 0) {
    throw "Build failed. Compiler exit code: $LASTEXITCODE"
}

Write-Host "Build complete: $output ($catalogRows shortcut records)" -ForegroundColor Green
if ($Run) {
    Start-Process -FilePath $output -WorkingDirectory $root
}
