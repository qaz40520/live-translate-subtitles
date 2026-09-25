$ErrorActionPreference = 'Stop'
$RegistrySubkey = 'Software\Mozilla\NativeMessagingHosts\com.livetranslatesubtitles.service'

foreach ($View in [Microsoft.Win32.RegistryView]::Registry32, [Microsoft.Win32.RegistryView]::Registry64) {
    $RegistryBase = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
        [Microsoft.Win32.RegistryHive]::CurrentUser,
        $View
    )
    try {
        $RegistryBase.DeleteSubKeyTree($RegistrySubkey, $false)
    }
    finally {
        $RegistryBase.Dispose()
    }
}

Write-Output 'Firefox native host registration removed.'
