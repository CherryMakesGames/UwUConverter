param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,

    [switch]$ElevatedTrustOnly
)

$ErrorActionPreference = "Stop"

$PackageName = "PinkSakuraStudios.UwUConverterShell"
$ModernDir = Join-Path $InstallDir "modern-shell"
$PackagePath = Join-Path $ModernDir "UwUConverterShell.msix"
$CertificatePath = Join-Path $ModernDir "UwUConverterShell.cer"
$CertificateState = Join-Path $ModernDir "trusted_dev_cert_thumbprint.txt"
$LogPath = Join-Path $ModernDir "registration.log"
$PowerShellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

function Write-Log {
    param([string]$Text)

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"

    Add-Content `
        -Path $LogPath `
        -Value ("[{0}] {1}" -f $Timestamp, $Text) `
        -Encoding UTF8
}

function Fail {
    param(
        [string]$Step,
        $ErrorObject
    )

    $Message = [string]$ErrorObject.Exception.Message
    $HResult = "0x{0:X8}" -f (
        $ErrorObject.Exception.HResult -band 0xFFFFFFFF
    )

    Write-Log ("FAILED STEP: " + $Step)
    Write-Log ("HRESULT: " + $HResult)
    Write-Log ("MESSAGE: " + $Message)

    Write-Error (
        "UwUConverter modern shell registration failed during "
        + $Step
        + ". "
        + $HResult
        + ": "
        + $Message
    )

    exit 1
}

New-Item `
    -ItemType Directory `
    -Path $ModernDir `
    -Force |
    Out-Null

if (!(Test-Path -LiteralPath $CertificatePath)) {
    Write-Log "Certificate file does not exist."
    Write-Error (
        "Modern shell certificate was not found: "
        + $CertificatePath
    )
    exit 1
}

# This branch is intentionally tiny. It runs only after a UAC prompt and only
# changes the machine Trusted People certificate store.
if ($ElevatedTrustOnly) {
    try {
        Write-Log "Elevated certificate-trust helper started."

        $Certificate = New-Object `
            -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2 `
            -ArgumentList $CertificatePath

        if (Test-Path -LiteralPath $CertificateState) {
            $OldThumbprint = (
                Get-Content `
                    -LiteralPath $CertificateState `
                    -Raw
            ).Trim()

            if (
                $OldThumbprint
                -and
                ($OldThumbprint -ne $Certificate.Thumbprint)
            ) {
                $OldMachineCert = (
                    "Cert:\LocalMachine\TrustedPeople\"
                    + $OldThumbprint
                )

                if (Test-Path $OldMachineCert) {
                    Write-Log (
                        "Removing previous machine-trusted development certificate: "
                        + $OldThumbprint
                    )

                    Remove-Item `
                        -Path $OldMachineCert `
                        -Force `
                        -ErrorAction Stop
                }
            }
        }

        $MachineCertPath = (
            "Cert:\LocalMachine\TrustedPeople\"
            + $Certificate.Thumbprint
        )

        if (!(Test-Path $MachineCertPath)) {
            Write-Log (
                "Importing certificate to LocalMachine\TrustedPeople."
            )

            Import-Certificate `
                -FilePath $CertificatePath `
                -CertStoreLocation "Cert:\LocalMachine\TrustedPeople" `
                -ErrorAction Stop |
                Out-Null
        }
        else {
            Write-Log (
                "Certificate is already present in "
                + "LocalMachine\TrustedPeople."
            )
        }

        if (!(Test-Path $MachineCertPath)) {
            throw (
                "Certificate import completed but the certificate "
                + "is not present in LocalMachine\TrustedPeople."
            )
        }

        Set-Content `
            -LiteralPath $CertificateState `
            -Value $Certificate.Thumbprint `
            -Encoding ASCII

        Write-Log (
            "Machine certificate trust verified: "
            + $Certificate.Thumbprint
        )

        exit 0
    }
    catch {
        Fail "elevated LocalMachine certificate trust" $_
    }
}

# Inno Setup creates the first log line before this script starts.
Write-Log "PowerShell registration script started."
Write-Log (
    "PowerShell version: "
    + $PSVersionTable.PSVersion.ToString()
)
Write-Log ("InstallDir: " + $InstallDir)
Write-Log ("PackagePath: " + $PackagePath)
Write-Log ("CertificatePath: " + $CertificatePath)

if (!(Test-Path -LiteralPath $PackagePath)) {
    Write-Log "Package file does not exist."
    Write-Error (
        "Modern shell package was not found: "
        + $PackagePath
    )
    exit 1
}

try {
    $ExistingPackages = @(
        Get-AppxPackage `
            -Name $PackageName `
            -ErrorAction SilentlyContinue
    )

    foreach ($ExistingPackage in $ExistingPackages) {
        Write-Log (
            "Removing existing package: "
            + $ExistingPackage.PackageFullName
        )

        Remove-AppxPackage `
            -Package $ExistingPackage.PackageFullName `
            -ErrorAction Stop
    }
}
catch {
    Fail "removing previous package" $_
}

try {
    $Certificate = New-Object `
        -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2 `
        -ArgumentList $CertificatePath

    Write-Log (
        "Certificate subject: "
        + $Certificate.Subject
    )
    Write-Log (
        "Certificate issuer: "
        + $Certificate.Issuer
    )
    Write-Log (
        "Certificate thumbprint: "
        + $Certificate.Thumbprint
    )

    if ($Certificate.Subject -eq $Certificate.Issuer) {
        Write-Log "Self-signed development certificate detected."

        # Clean the old CurrentUser trust entry created by earlier UwUConverter
        # development builds. Current Windows MSIX deployment requires the
        # test-signing certificate in the machine Trusted People store.
        if (Test-Path -LiteralPath $CertificateState) {
            $OldThumbprint = (
                Get-Content `
                    -LiteralPath $CertificateState `
                    -Raw
            ).Trim()

            if ($OldThumbprint) {
                $OldUserCert = (
                    "Cert:\CurrentUser\TrustedPeople\"
                    + $OldThumbprint
                )

                if (Test-Path $OldUserCert) {
                    Write-Log (
                        "Removing old CurrentUser certificate: "
                        + $OldThumbprint
                    )

                    Remove-Item `
                        -Path $OldUserCert `
                        -Force `
                        -ErrorAction SilentlyContinue
                }
            }
        }

        $MachineCertificatePath = (
            "Cert:\LocalMachine\TrustedPeople\"
            + $Certificate.Thumbprint
        )

        if (!(Test-Path $MachineCertificatePath)) {
            Write-Log (
                "Certificate is not trusted in "
                + "LocalMachine\TrustedPeople."
            )
            Write-Log (
                "Requesting UAC elevation only for certificate trust."
            )

            $Arguments = @(
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                ('"' + $PSCommandPath + '"'),
                "-InstallDir",
                ('"' + $InstallDir + '"'),
                "-ElevatedTrustOnly"
            )

            $ElevatedProcess = Start-Process `
                -FilePath $PowerShellExe `
                -Verb RunAs `
                -ArgumentList $Arguments `
                -Wait `
                -PassThru `
                -ErrorAction Stop

            Write-Log (
                "Elevated certificate helper exit code: "
                + $ElevatedProcess.ExitCode
            )

            if ($ElevatedProcess.ExitCode -ne 0) {
                throw (
                    "The elevated certificate trust helper returned exit code "
                    + $ElevatedProcess.ExitCode
                    + "."
                )
            }
        }

        if (!(Test-Path $MachineCertificatePath)) {
            throw (
                "The package certificate is still not present in "
                + "LocalMachine\TrustedPeople after elevation."
            )
        }

        Write-Log (
            "Certificate is trusted in LocalMachine\TrustedPeople."
        )
    }
    else {
        Write-Log (
            "Certificate is not self-signed. "
            + "Windows will validate its normal trust chain."
        )
    }
}
catch {
    Fail "trusting package certificate" $_
}

try {
    Write-Log "Calling Add-AppxPackage."

    Add-AppxPackage `
        -Path $PackagePath `
        -ExternalLocation $InstallDir `
        -ForceApplicationShutdown `
        -ErrorAction Stop

    $RegisteredPackage = Get-AppxPackage `
        -Name $PackageName `
        -ErrorAction SilentlyContinue

    if (!$RegisteredPackage) {
        throw (
            "Add-AppxPackage completed but the package "
            + "is not registered for the current user."
        )
    }

    Write-Log (
        "Registered package: "
        + $RegisteredPackage.PackageFullName
    )
    Write-Log "SUCCESS"
}
catch {
    Fail "Add-AppxPackage" $_
}

exit 0
