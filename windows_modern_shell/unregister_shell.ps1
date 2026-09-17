param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,

    [switch]$CertificateOnly
)

$ErrorActionPreference = "Continue"

$PackageName = "CherryMakesGames.UwUConverterShell"
$ModernDir = Join-Path $InstallDir "modern-shell"
$CertificateState = Join-Path $ModernDir "trusted_dev_cert_thumbprint.txt"
$SettingsPath = "HKCU:\Software\Pink Sakura Studios\UwUConverter"
$ModernShellValue = "ModernShellRegistered"

if ($CertificateOnly) {
    if (Test-Path -LiteralPath $CertificateState) {
        $Thumbprint = (Get-Content -LiteralPath $CertificateState -Raw).Trim()

        if ($Thumbprint) {
            $MachineCertificatePath = "Cert:\LocalMachine\TrustedPeople\" + $Thumbprint

            if (Test-Path $MachineCertificatePath) {
                Remove-Item -Path $MachineCertificatePath -Force -ErrorAction SilentlyContinue
            }
        }
    }

    exit 0
}

if (Test-Path $SettingsPath) {
    Remove-ItemProperty `
        -Path $SettingsPath `
        -Name $ModernShellValue `
        -ErrorAction SilentlyContinue
}

$Packages = @(
    Get-AppxPackage -ErrorAction SilentlyContinue |
        Where-Object {
            ($_.Name -eq $PackageName) -or
            ($_.Name -like "*UwUConverterShell*") -or
            ($_.PackageFullName -like "*UwUConverterShell*") -or
            ($_.PackageFamilyName -like "*UwUConverterShell*")
        }
)

foreach ($Package in $Packages) {
    Remove-AppxPackage `
        -Package $Package.PackageFullName `
        -ErrorAction SilentlyContinue
}

exit 0
