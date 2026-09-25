param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-p]{32}$')]
    [string]$ExtensionId
)

$ErrorActionPreference = 'Stop'
$ServiceRoot = Split-Path -Parent $PSScriptRoot
$RepositoryRoot = Split-Path -Parent (Split-Path -Parent $ServiceRoot)
$HostExecutable = Join-Path $RepositoryRoot '.venv\Scripts\live-translate-native-host.exe'

if (-not (Test-Path -LiteralPath $HostExecutable)) {
    throw "Native host executable not found: $HostExecutable. Install apps/local-service[stt] in .venv first."
}

$InstallRoot = Join-Path $env:LOCALAPPDATA 'LiveTranslateSubtitles\native-host'
New-Item -ItemType Directory -Force -Path $InstallRoot | Out-Null
$ManifestPath = Join-Path $InstallRoot 'com.livetranslatesubtitles.service.json'

$Manifest = [ordered]@{
    name = 'com.livetranslatesubtitles.service'
    description = 'Local speech recognition service for Live Translate Subtitles'
    path = $HostExecutable
    type = 'stdio'
    allowed_origins = @("chrome-extension://$ExtensionId/")
}

$Manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ManifestPath -Encoding utf8
$RegistryPath = 'HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.livetranslatesubtitles.service'
New-Item -Force -Path $RegistryPath | Out-Null
Set-Item -LiteralPath $RegistryPath -Value $ManifestPath

Write-Output "Registered Chrome native host for extension $ExtensionId"
Write-Output "Manifest: $ManifestPath"
