param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,

    [switch]$CertificateOnly
)

$ErrorActionPreference = "Continue"

$PackageName = "PinkSakuraStudios.UwUConverterShell"
$ModernDir = Join-Path $InstallDir "modern-shell"
$CertificateState = Join-Path $ModernDir "trusted_dev_cert_thumbprint.txt"

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

Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-AppxPackage -Package $_.PackageFullName -ErrorAction SilentlyContinue
    }

exit 0
