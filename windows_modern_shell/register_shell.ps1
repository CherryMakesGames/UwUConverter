param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir
)

$ErrorActionPreference = "Stop"

$PackageName = "CherryMakesGames.UwUConverterShell"
$ModernDir = Join-Path $InstallDir "modern-shell"
$PackagePath = Join-Path $ModernDir "UwUConverterShell.msix"
$CertificatePath = Join-Path $ModernDir "UwUConverterShell.cer"
$CertificateState = Join-Path $ModernDir "trusted_dev_cert_thumbprint.txt"
$LogPath = Join-Path $ModernDir "registration.log"
$SettingsPath = "HKCU:\\Software\\Pink Sakura Studios\\UwUConverter"
$ModernShellValue = "ModernShellRegistered"

function Write-Log {
    param([string]$Text)

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    Add-Content -Path $LogPath -Value ("[{0}] {1}" -f $Timestamp, $Text) -Encoding UTF8
}

function Fail {
    param(
        [string]$Step,
        $ErrorObject
    )

    $Message = [string]$ErrorObject.Exception.Message
    $HResult = "0x{0:X8}" -f ($ErrorObject.Exception.HResult -band 0xFFFFFFFF)

    Write-Log ("FAILED STEP: " + $Step)
    Write-Log ("HRESULT: " + $HResult)
    Write-Log ("MESSAGE: " + $Message)

    Write-Error ("UwUConverter modern shell registration failed during " + $Step + ". " + $HResult + ": " + $Message)
    exit 1
}

New-Item -Path $SettingsPath -Force | Out-Null
Set-ItemProperty `
    -Path $SettingsPath `
    -Name $ModernShellValue `
    -Type DWord `
    -Value 0 `
    -Force

Write-Log "PowerShell registration script started."
Write-Log ("PowerShell version: " + $PSVersionTable.PSVersion.ToString())
Write-Log ("InstallDir: " + $InstallDir)
Write-Log ("PackagePath: " + $PackagePath)
Write-Log ("CertificatePath: " + $CertificatePath)

if (!(Test-Path -LiteralPath $PackagePath)) {
    Write-Log "Package file does not exist."
    Write-Error ("Modern shell package was not found: " + $PackagePath)
    exit 1
}

if (!(Test-Path -LiteralPath $CertificatePath)) {
    Write-Log "Certificate file does not exist."
    Write-Error ("Modern shell certificate was not found: " + $CertificatePath)
    exit 1
}

try {
    $Certificate = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2 -ArgumentList $CertificatePath

    Write-Log ("Certificate subject: " + $Certificate.Subject)
    Write-Log ("Certificate thumbprint: " + $Certificate.Thumbprint)

    $MachineCertificatePath = "Cert:\LocalMachine\TrustedPeople\" + $Certificate.Thumbprint

    if (!(Test-Path $MachineCertificatePath)) {
        throw "The package signing certificate is not present in LocalMachine\TrustedPeople after the installer trust step."
    }

    Write-Log "Certificate trust verified in LocalMachine\TrustedPeople."

    Set-Content -LiteralPath $CertificateState -Value $Certificate.Thumbprint -Encoding ASCII
}
catch {
    Fail "verifying package certificate trust" $_
}

try {
    $ExistingPackages = @(Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue)

    foreach ($ExistingPackage in $ExistingPackages) {
        Write-Log ("Removing existing package: " + $ExistingPackage.PackageFullName)
        Remove-AppxPackage -Package $ExistingPackage.PackageFullName -ErrorAction Stop
    }
}
catch {
    Fail "removing previous package" $_
}

try {
    Write-Log "Calling Add-AppxPackage."

    Add-AppxPackage `
        -Path $PackagePath `
        -ExternalLocation $InstallDir `
        -ForceApplicationShutdown `
        -ErrorAction Stop

    $RegisteredPackage = Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue

    if (!$RegisteredPackage) {
        throw "Add-AppxPackage completed but the package is not registered for the current user."
    }

    Write-Log ("Registered package: " + $RegisteredPackage.PackageFullName)

    # Windows 11 can surface the old static registry verbs in the modern
    # context menu, producing a second UwUConverter root. Enumerate the actual
    # SystemFileAssociations children and remove our exact keys literally.
    # This is more reliable than a wildcard Registry-provider path.
    $SystemFileAssociations = (
        "Registry::HKEY_CURRENT_USER"
        + "\Software\Classes\SystemFileAssociations"
    )

    if (Test-Path -LiteralPath $SystemFileAssociations) {
        Get-ChildItem `
            -LiteralPath $SystemFileAssociations `
            -ErrorAction SilentlyContinue |
            ForEach-Object {
                $ConversionKey = Join-Path `
                    $_.PSPath `
                    "shell\UwUConverter"

                $ArchiveKey = Join-Path `
                    $_.PSPath `
                    "shell\UwUConverterExtract"

                if (Test-Path -LiteralPath $ConversionKey) {
                    Remove-Item `
                        -LiteralPath $ConversionKey `
                        -Recurse `
                        -Force `
                        -ErrorAction SilentlyContinue
                }

                if (Test-Path -LiteralPath $ArchiveKey) {
                    Remove-Item `
                        -LiteralPath $ArchiveKey `
                        -Recurse `
                        -Force `
                        -ErrorAction SilentlyContinue
                }
            }
    }

    $LegacyLiteralKeys = @(
        (
            "Registry::HKEY_CURRENT_USER"
            + "\Software\Classes\Directory"
            + "\shell\UwUConverter"
        ),
        (
            "Registry::HKEY_CURRENT_USER"
            + "\Software\Classes\AllFilesystemObjects"
            + "\shell\UwUConverterZipSelection"
        )
    )

    foreach ($LegacyKey in $LegacyLiteralKeys) {
        if (Test-Path -LiteralPath $LegacyKey) {
            Remove-Item `
                -LiteralPath $LegacyKey `
                -Recurse `
                -Force `
                -ErrorAction SilentlyContinue
        }
    }

    Set-ItemProperty `
        -Path $SettingsPath `
        -Name $ModernShellValue `
        -Type DWord `
        -Value 1 `
        -Force

    Write-Log "Removed legacy duplicate context-menu registrations using literal enumeration."
    Write-Log "ModernShellRegistered=1"
    Write-Log "SUCCESS"
}
catch {
    Fail "Add-AppxPackage" $_
}

exit 0
