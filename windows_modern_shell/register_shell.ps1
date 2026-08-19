param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir
)

$ErrorActionPreference = "Stop"

$packageName = "PinkSakuraStudios.UwUConverterShell"
$modernDir = Join-Path $InstallDir "modern-shell"
$packagePath = Join-Path $modernDir "UwUConverterShell.msix"
$certificatePath = Join-Path $modernDir "UwUConverterShell.cer"
$certificateState = Join-Path $modernDir "trusted_dev_cert_thumbprint.txt"

if (!(Test-Path $packagePath)) {
    throw "Modern shell package was not found: $packagePath"
}

if (!(Test-Path $certificatePath)) {
    throw "Modern shell certificate was not found: $certificatePath"
}

# Remove a previous registration before replacing it.
Get-AppxPackage -Name $packageName -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-AppxPackage -Package $_.PackageFullName -ErrorAction Stop
    }

# Remove only the exact development certificate that a previous UwUConverter
# build imported.
if (Test-Path $certificateState) {
    $oldThumbprint = (Get-Content $certificateState -Raw).Trim()

    if ($oldThumbprint) {
        $oldCert = "Cert:\CurrentUser\TrustedPeople\$oldThumbprint"
        if (Test-Path $oldCert) {
            Remove-Item $oldCert -Force -ErrorAction SilentlyContinue
        }
    }

    Remove-Item $certificateState -Force -ErrorAction SilentlyContinue
}

$certificate = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($certificatePath)

# CI/local builds use a self-signed package certificate.
if ($certificate.Subject -eq $certificate.Issuer) {
    Import-Certificate `
        -FilePath $certificatePath `
        -CertStoreLocation "Cert:\CurrentUser\TrustedPeople" |
        Out-Null

    Set-Content `
        -Path $certificateState `
        -Value $certificate.Thumbprint `
        -Encoding ASCII
}

Add-AppxPackage `
    -Path $packagePath `
    -ExternalLocation $InstallDir
