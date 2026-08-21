param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir,

    [switch]$ElevatedCertificateOnly
)

$ErrorActionPreference = "Continue"

$PackageName = "PinkSakuraStudios.UwUConverterShell"
$ModernDir = Join-Path $InstallDir "modern-shell"
$CertificateState = Join-Path $ModernDir "trusted_dev_cert_thumbprint.txt"
$PowerShellExe = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"

if ($ElevatedCertificateOnly) {
    if (Test-Path -LiteralPath $CertificateState) {
        $Thumbprint = (
            Get-Content `
                -LiteralPath $CertificateState `
                -Raw
        ).Trim()

        if ($Thumbprint) {
            $MachineCert = (
                "Cert:\LocalMachine\TrustedPeople\"
                + $Thumbprint
            )

            if (Test-Path $MachineCert) {
                Remove-Item `
                    -Path $MachineCert `
                    -Force `
                    -ErrorAction SilentlyContinue
            }
        }
    }

    exit 0
}

Get-AppxPackage `
    -Name $PackageName `
    -ErrorAction SilentlyContinue |
    ForEach-Object {
        Remove-AppxPackage `
            -Package $_.PackageFullName `
            -ErrorAction SilentlyContinue
    }

if (Test-Path -LiteralPath $CertificateState) {
    $Thumbprint = (
        Get-Content `
            -LiteralPath $CertificateState `
            -Raw
    ).Trim()

    if ($Thumbprint) {
        # Clean an old per-user trust entry if an earlier development build
        # created one.
        $UserCert = (
            "Cert:\CurrentUser\TrustedPeople\"
            + $Thumbprint
        )

        if (Test-Path $UserCert) {
            Remove-Item `
                -Path $UserCert `
                -Force `
                -ErrorAction SilentlyContinue
        }

        # Machine TrustedPeople requires elevation. Ask only for this cleanup.
        $MachineCert = (
            "Cert:\LocalMachine\TrustedPeople\"
            + $Thumbprint
        )

        if (Test-Path $MachineCert) {
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
                "-ElevatedCertificateOnly"
            )

            try {
                Start-Process `
                    -FilePath $PowerShellExe `
                    -Verb RunAs `
                    -ArgumentList $Arguments `
                    -Wait `
                    -ErrorAction SilentlyContinue
            }
            catch {
                # The package itself has already been unregistered. If the
                # user cancels UAC here, leave the development trust entry.
            }
        }
    }

    Remove-Item `
        -LiteralPath $CertificateState `
        -Force `
        -ErrorAction SilentlyContinue
}

exit 0
