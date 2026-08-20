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
$logPath = Join-Path $modernDir "registration.log"

function Write-RegistrationLog([string]$Message) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    Add-Content `
        -Path $logPath `
        -Value ("[{0}] {1}" -f $timestamp, $Message) `
        -Encoding UTF8
}

function Fail-Registration(
    [string]$Step,
    [System.Exception]$Exception
) {
    $hresult = "0x{0:X8}" -f ($Exception.HResult -band 0xFFFFFFFF)

    Write-RegistrationLog ("FAILED STEP: " + $Step)
    Write-RegistrationLog ("HRESULT: " + $hresult)
    Write-RegistrationLog ("MESSAGE: " + $Exception.Message)

    if ($Exception.InnerException) {
        Write-RegistrationLog (
            "INNER: " + $Exception.InnerException.Message
        )
    }

    Write-Error (
        "UwUConverter modern shell registration failed during "
        + $Step
        + ". "
        + $hresult
        + ": "
        + $Exception.Message
    )

    exit 1
}

New-Item -ItemType Directory -Force $modernDir | Out-Null

Set-Content `
    -Path $logPath `
    -Value "UwUConverter Windows 11 modern context-menu registration" `
    -Encoding UTF8

Write-RegistrationLog ("InstallDir: " + $InstallDir)
Write-RegistrationLog ("Package: " + $packagePath)
Write-RegistrationLog ("Certificate: " + $certificatePath)

if (!(Test-Path $packagePath)) {
    Write-RegistrationLog "Package file is missing."
    Write-Error "Modern shell package was not found: $packagePath"
    exit 1
}

if (!(Test-Path $certificatePath)) {
    Write-RegistrationLog "Certificate file is missing."
    Write-Error "Modern shell certificate was not found: $certificatePath"
    exit 1
}

try {
    $existingPackages = @(
        Get-AppxPackage `
            -Name $packageName `
            -ErrorAction SilentlyContinue
    )

    foreach ($existing in $existingPackages) {
        Write-RegistrationLog (
            "Removing previous package: "
            + $existing.PackageFullName
        )

        Remove-AppxPackage `
            -Package $existing.PackageFullName `
            -ErrorAction Stop
    }
}
catch {
    Fail-Registration "removing previous package" $_.Exception
}

# Remove only the exact development certificate imported by a previous
# UwUConverter build. Production certificates are never removed here.
try {
    if (Test-Path $certificateState) {
        $oldThumbprint = (Get-Content $certificateState -Raw).Trim()

        if ($oldThumbprint) {
            $oldCert = "Cert:\CurrentUser\TrustedPeople\$oldThumbprint"

            if (Test-Path $oldCert) {
                Write-RegistrationLog (
                    "Removing previous development certificate: "
                    + $oldThumbprint
                )

                Remove-Item `
                    $oldCert `
                    -Force `
                    -ErrorAction SilentlyContinue
            }
        }

        Remove-Item `
            $certificateState `
            -Force `
            -ErrorAction SilentlyContinue
    }
}
catch {
    Fail-Registration "cleaning previous certificate" $_.Exception
}

try {
    $certificate = New-Object `
        System.Security.Cryptography.X509Certificates.X509Certificate2(
            $certificatePath
        )

    Write-RegistrationLog (
        "Package certificate subject: "
        + $certificate.Subject
    )
    Write-RegistrationLog (
        "Package certificate issuer: "
        + $certificate.Issuer
    )
    Write-RegistrationLog (
        "Package certificate thumbprint: "
        + $certificate.Thumbprint
    )

    # Microsoft documents CurrentUser\TrustedPeople for development
    # self-signed sparse-package certificates.
    if ($certificate.Subject -eq $certificate.Issuer) {
        Write-RegistrationLog (
            "Importing self-signed certificate into "
            + "CurrentUser\\TrustedPeople."
        )

        Import-Certificate `
            -FilePath $certificatePath `
            -CertStoreLocation "Cert:\CurrentUser\TrustedPeople" `
            -ErrorAction Stop |
            Out-Null

        $trustedPath = (
            "Cert:\CurrentUser\TrustedPeople\"
            + $certificate.Thumbprint
        )

        if (!(Test-Path $trustedPath)) {
            throw (
                "Certificate import completed but the certificate "
                + "is not present in CurrentUser\\TrustedPeople."
            )
        }

        Set-Content `
            -Path $certificateState `
            -Value $certificate.Thumbprint `
            -Encoding ASCII

        Write-RegistrationLog "Certificate trust verified."
    }
    else {
        Write-RegistrationLog (
            "Certificate is not self-signed; assuming normal "
            + "Windows trust-chain validation."
        )
    }
}
catch {
    Fail-Registration "trusting package certificate" $_.Exception
}

try {
    Write-RegistrationLog "Registering sparse MSIX package."

    # This is the Microsoft-documented per-user sparse-package registration.
    # ForceApplicationShutdown also makes replacement installs more reliable
    # when Explorer still has an older shell-extension instance loaded.
    Add-AppxPackage `
        -Path $packagePath `
        -ExternalLocation $InstallDir `
        -ForceApplicationShutdown `
        -ErrorAction Stop

    $registered = Get-AppxPackage `
        -Name $packageName `
        -ErrorAction SilentlyContinue

    if (!$registered) {
        throw (
            "Add-AppxPackage returned successfully, but "
            + $packageName
            + " is not registered for the current user."
        )
    }

    Write-RegistrationLog (
        "Registered package: "
        + $registered.PackageFullName
    )
    Write-RegistrationLog "SUCCESS"
}
catch {
    Fail-Registration "Add-AppxPackage" $_.Exception
}

exit 0
