param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir
)

$ErrorActionPreference = "Stop"

$PackageName = "CherryMakesGames.UwUConverterShell"
$ModernDir = Join-Path -Path $InstallDir -ChildPath "modern-shell"
$PackagePath = Join-Path -Path $ModernDir -ChildPath "UwUConverterShell.msix"
$CertificatePath = Join-Path -Path $ModernDir -ChildPath "UwUConverterShell.cer"
$CertificateState = Join-Path -Path $ModernDir -ChildPath "trusted_dev_cert_thumbprint.txt"
$LogPath = Join-Path -Path $ModernDir -ChildPath "registration.log"
$SettingsPath = "HKCU:\Software\Pink Sakura Studios\UwUConverter"
$ModernShellValue = "ModernShellRegistered"

function Write-Log {
    param(
        [string]$Text
    )

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $Line = "[{0}] {1}" -f $Timestamp, $Text
    Add-Content -Path $LogPath -Value $Line -Encoding UTF8
}

function Fail {
    param(
        [string]$Step,
        $ErrorObject
    )

    $Message = [string]$ErrorObject.Exception.Message
    $HResultValue = $ErrorObject.Exception.HResult -band 0xFFFFFFFF
    $HResult = "0x{0:X8}" -f $HResultValue

    Write-Log -Text ("FAILED STEP: " + $Step)
    Write-Log -Text ("HRESULT: " + $HResult)
    Write-Log -Text ("MESSAGE: " + $Message)

    Write-Error ("UwUConverter modern shell registration failed during " + $Step + ". " + $HResult + ": " + $Message)
    exit 1
}

try {
    New-Item -Path $SettingsPath -Force | Out-Null

    New-ItemProperty `
        -Path $SettingsPath `
        -Name $ModernShellValue `
        -PropertyType DWord `
        -Value 0 `
        -Force |
        Out-Null
}
catch {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $InitError = [string]$_.Exception.Message

    Add-Content `
        -Path $LogPath `
        -Value ("[" + $Timestamp + "] FAILED STEP: initialize ModernShellRegistered marker") `
        -Encoding UTF8

    Add-Content `
        -Path $LogPath `
        -Value ("[" + $Timestamp + "] MESSAGE: " + $InitError) `
        -Encoding UTF8

    exit 1
}

Write-Log -Text "PowerShell registration script started."
Write-Log -Text "ModernShellRegistered marker initialized successfully."
Write-Log -Text ("PowerShell version: " + $PSVersionTable.PSVersion.ToString())
Write-Log -Text ("InstallDir: " + $InstallDir)
Write-Log -Text ("PackagePath: " + $PackagePath)
Write-Log -Text ("CertificatePath: " + $CertificatePath)

if (!(Test-Path -LiteralPath $PackagePath)) {
    Write-Log -Text "Package file does not exist."
    Write-Error ("Modern shell package was not found: " + $PackagePath)
    exit 1
}

if (!(Test-Path -LiteralPath $CertificatePath)) {
    Write-Log -Text "Certificate file does not exist."
    Write-Error ("Modern shell certificate was not found: " + $CertificatePath)
    exit 1
}

try {
    $Certificate = New-Object -TypeName System.Security.Cryptography.X509Certificates.X509Certificate2 -ArgumentList $CertificatePath

    Write-Log -Text ("Certificate subject: " + $Certificate.Subject)
    Write-Log -Text ("Certificate thumbprint: " + $Certificate.Thumbprint)

    $MachineCertificatePath = "Cert:\LocalMachine\TrustedPeople\" + $Certificate.Thumbprint

    if (!(Test-Path -LiteralPath $MachineCertificatePath)) {
        throw "The package signing certificate is not present in LocalMachine\TrustedPeople after the installer trust step."
    }

    Write-Log -Text "Certificate trust verified in LocalMachine\TrustedPeople."

    Set-Content `
        -LiteralPath $CertificateState `
        -Value $Certificate.Thumbprint `
        -Encoding ASCII
}
catch {
    Fail -Step "verifying package certificate trust" -ErrorObject $_
}

try {
    $ExistingPackages = @(Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue)

    foreach ($ExistingPackage in $ExistingPackages) {
        Write-Log -Text ("Removing existing package: " + $ExistingPackage.PackageFullName)

        Remove-AppxPackage `
            -Package $ExistingPackage.PackageFullName `
            -ErrorAction Stop
    }
}
catch {
    Fail -Step "removing previous package" -ErrorObject $_
}

try {
    Write-Log -Text "Calling Add-AppxPackage."

    Add-AppxPackage `
        -Path $PackagePath `
        -ExternalLocation $InstallDir `
        -ForceApplicationShutdown `
        -ErrorAction Stop

    $RegisteredPackage = Get-AppxPackage -Name $PackageName -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($null -eq $RegisteredPackage) {
        throw "Add-AppxPackage completed but the package is not registered for the current user."
    }

    Write-Log -Text ("Registered package: " + $RegisteredPackage.PackageFullName)

    $SystemFileAssociations = "Registry::HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations"

    if (Test-Path -LiteralPath $SystemFileAssociations) {
        $AssociationKeys = Get-ChildItem -LiteralPath $SystemFileAssociations -ErrorAction SilentlyContinue

        foreach ($AssociationKey in $AssociationKeys) {
            $ConversionKey = Join-Path -Path $AssociationKey.PSPath -ChildPath "shell\UwUConverter"
            $ArchiveKey = Join-Path -Path $AssociationKey.PSPath -ChildPath "shell\UwUConverterExtract"

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
        "Registry::HKEY_CURRENT_USER\Software\Classes\Directory\shell\UwUConverter",
        "Registry::HKEY_CURRENT_USER\Software\Classes\Directory\shell\UwUConverterExtract",
        "Registry::HKEY_CURRENT_USER\Software\Classes\AllFilesystemObjects\shell\UwUConverterZipSelection",
        "Registry::HKEY_CURRENT_USER\Software\Classes\*\shell\UwUConverter",
        "Registry::HKEY_CURRENT_USER\Software\Classes\*\shell\UwUConverterExtract"
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

    New-ItemProperty `
        -Path $SettingsPath `
        -Name $ModernShellValue `
        -PropertyType DWord `
        -Value 1 `
        -Force |
        Out-Null

    Write-Log -Text "Removed legacy duplicate context-menu registrations."
    Write-Log -Text "ModernShellRegistered=1"
    Write-Log -Text "SUCCESS"
}
catch {
    Fail -Step "Add-AppxPackage / legacy menu cleanup" -ErrorObject $_
}

exit 0
