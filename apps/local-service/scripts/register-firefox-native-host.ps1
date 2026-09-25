param(
    [string]$ExtensionId = 'live-translate-subtitles@example.invalid'
)

$ErrorActionPreference = 'Stop'
$ServiceRoot = Split-Path -Parent $PSScriptRoot
$RepositoryRoot = Split-Path -Parent (Split-Path -Parent $ServiceRoot)
$HostExecutable = Join-Path $RepositoryRoot '.venv\Scripts\live-translate-native-host.exe'

if (-not (Test-Path -LiteralPath $HostExecutable)) {
    throw "Native host executable not found: $HostExecutable. Install apps/local-service[models] in .venv first."
}

$InstallRoot = Join-Path $env:LOCALAPPDATA 'LiveTranslateSubtitles\native-host'
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
$ManifestPath = Join-Path $InstallRoot 'com.livetranslatesubtitles.service.firefox.json'
$LauncherPath = Join-Path $InstallRoot 'live-translate-native-host-launcher.exe'
$PythonPathFile = Join-Path $InstallRoot 'python-path.txt'
$LauncherSource = Join-Path $PSScriptRoot 'native-host-launcher.cs'
$Compiler = 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe'

if (-not (Test-Path -LiteralPath $Compiler)) {
    throw "C# compiler not found: $Compiler"
}

if (-not (Test-Path -LiteralPath $LauncherPath)) {
    & $Compiler /nologo /target:exe "/out:$LauncherPath" $LauncherSource
    if ($LASTEXITCODE -ne 0) {
        throw 'Failed to compile the native host launcher.'
    }
}

$VenvPython = Join-Path $RepositoryRoot '.venv\Scripts\python.exe'
Set-Content -LiteralPath $PythonPathFile -Value $VenvPython -Encoding utf8

$Manifest = [ordered]@{
    name = 'com.livetranslatesubtitles.service'
    description = 'Local speech recognition service for Live Translate Subtitles'
    path = $LauncherPath
    type = 'stdio'
    allowed_extensions = @($ExtensionId)
}

$Manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ManifestPath -Encoding utf8
$RegistrySubkey = 'Software\Mozilla\NativeMessagingHosts\com.livetranslatesubtitles.service'
foreach ($View in [Microsoft.Win32.RegistryView]::Registry32, [Microsoft.Win32.RegistryView]::Registry64) {
    $RegistryBase = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::CurrentUser,
        $View
    )
    try {
        $RegistryKey = $RegistryBase.CreateSubKey($RegistrySubkey)
        try {
            $RegistryKey.SetValue('', $ManifestPath, [Microsoft.Win32.RegistryValueKind]::String)
        }
        finally {
            $RegistryKey.Dispose()
        }
    }
    finally {
        $RegistryBase.Dispose()
    }
}

Write-Output "Registered Firefox native host for extension $ExtensionId"
Write-Output "Manifest: $ManifestPath"
Write-Output "Launcher: $LauncherPath"
