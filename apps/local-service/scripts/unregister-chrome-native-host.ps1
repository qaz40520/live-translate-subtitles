$ErrorActionPreference = 'Stop'
$RegistryPath = 'HKCU:\Software\Google\Chrome\NativeMessagingHosts\com.livetranslatesubtitles.service'

if (Test-Path -LiteralPath $RegistryPath) {
    Remove-Item -LiteralPath $RegistryPath -Recurse
}

Write-Output 'Chrome native host registration removed.'

