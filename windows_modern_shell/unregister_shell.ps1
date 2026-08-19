param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir
)

$ErrorActionPreference = "Continue"

$packageName = "CherryMakesGames.UwUConverterShell"
$certificateState = Join-Path $InstallDir "modern-shell\trusted_dev_cert_thumbprint.txt"

Get-AppxPackage -Name $packageName -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-AppxPackage -Package $_.PackageFullName -ErrorAction SilentlyContinue
    }

if (Test-Path $certificateState) {
    $thumbprint = (Get-Content $certificateState -Raw).Trim()

    if ($thumbprint) {
        $certificatePath = "Cert:\CurrentUser\TrustedPeople\$thumbprint"

        if (Test-Path $certificatePath) {
            Remove-Item $certificatePath -Force -ErrorAction SilentlyContinue
        }
    }

    Remove-Item $certificateState -Force -ErrorAction SilentlyContinue
}
