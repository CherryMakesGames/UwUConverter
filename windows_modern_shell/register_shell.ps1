param(
    [Parameter(Mandatory = $true)]
    [string]$InstallDir
)

$ErrorActionPreference = "Stop"

$ExpectedPackageName = "CherryMakesGames.UwUConverterShell"
$PackageName = $ExpectedPackageName
$ModernDir = Join-Path -Path $InstallDir -ChildPath "modern-shell"
$PackagePath = Join-Path -Path $ModernDir -ChildPath "UwUConverterShell.msix"
$CertificatePath = Join-Path -Path $ModernDir -ChildPath "UwUConverterShell.cer"
$CertificateState = Join-Path -Path $ModernDir -ChildPath "trusted_dev_cert_thumbprint.txt"
$LogPath = Join-Path -Path $ModernDir -ChildPath "registration.log"
$SettingsPath = "HKCU:\Software\Pink Sakura Studios\UwUConverter"
$ModernShellValue = "ModernShellRegistered"

function Get-PackageIdentityName {
    param(
        [string]$MsixPath
    )

    Add-Type -AssemblyName System.IO.Compression.FileSystem

    $Archive = [System.IO.Compression.ZipFile]::OpenRead($MsixPath)

    try {
        $ManifestEntry = $Archive.GetEntry("AppxManifest.xml")

        if ($null -eq $ManifestEntry) {
            throw "AppxManifest.xml was not found inside the MSIX."
        }

        $Stream = $ManifestEntry.Open()
        $Reader = New-Object System.IO.StreamReader($Stream)

        try {
            $ManifestText = $Reader.ReadToEnd()
        }
        finally {
            $Reader.Dispose()
            $Stream.Dispose()
        }
    }
    finally {
        $Archive.Dispose()
    }

    $IdentityMatch = [regex]::Match(
        $ManifestText,
        '<Identity\s+[^>]*Name="([^"]+)"'
    )

    if (!$IdentityMatch.Success) {
        throw "Could not read the Identity Name from AppxManifest.xml."
    }

    return $IdentityMatch.Groups[1].Value
}


function Get-MatchingPackages {
    param(
        [string]$IdentityName
    )

    $Packages = @(Get-AppxPackage -ErrorAction SilentlyContinue)
    $Matches = @()

    foreach ($Package in $Packages) {
        $NameMatches = $Package.Name -eq $IdentityName

        $FullNameMatches = $false

        if ($Package.PackageFullName) {
            $FullNameMatches = $Package.PackageFullName.StartsWith(
                $IdentityName + "_",
                [System.StringComparison]::OrdinalIgnoreCase
            )
        }

        $FamilyMatches = $false

        if ($Package.PackageFamilyName) {
            $FamilyMatches = $Package.PackageFamilyName.StartsWith(
                $IdentityName + "_",
                [System.StringComparison]::OrdinalIgnoreCase
            )
        }

        if (
            $NameMatches -or
            $FullNameMatches -or
            $FamilyMatches
        ) {
            $Matches += $Package
        }
    }

    return $Matches
}


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
    $PackageName = Get-PackageIdentityName -MsixPath $PackagePath
    Write-Log -Text ("MSIX identity name: " + $PackageName)

    if ($PackageName -ne $ExpectedPackageName) {
        Write-Log -Text (
            "NOTE: package identity differs from the historical expected name: "
            + $ExpectedPackageName
        )
    }
}
catch {
    Fail -Step "reading MSIX package identity" -ErrorObject $_
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
    $ExistingPackages = @(
        Get-MatchingPackages -IdentityName $PackageName
    )

    foreach ($ExistingPackage in $ExistingPackages) {
        Write-Log -Text (
            "Removing existing package: "
            + $ExistingPackage.PackageFullName
        )

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

    $RegisteredPackage = $null

    for ($Attempt = 1; $Attempt -le 20; $Attempt++) {
        $RegisteredPackage = @(
            Get-MatchingPackages -IdentityName $PackageName
        ) | Select-Object -First 1

        if ($null -ne $RegisteredPackage) {
            break
        }

        Start-Sleep -Milliseconds 250
    }

    if ($null -eq $RegisteredPackage) {
        Write-Log -Text (
            "Package verification still failed after Add-AppxPackage. "
            + "Dumping current-user UwUConverter-like packages:"
        )

        $Candidates = @(
            Get-AppxPackage -ErrorAction SilentlyContinue |
                Where-Object {
                    ($_.Name -like "*UwUConverter*") -or
                    ($_.PackageFullName -like "*UwUConverter*") -or
                    ($_.PackageFamilyName -like "*UwUConverter*")
                }
        )

        if ($Candidates.Count -eq 0) {
            Write-Log -Text "No UwUConverter-like AppX packages were visible to the current user."
        }

        foreach ($Candidate in $Candidates) {
            Write-Log -Text (
                "Candidate package: Name="
                + $Candidate.Name
                + "; FullName="
                + $Candidate.PackageFullName
                + "; Family="
                + $Candidate.PackageFamilyName
            )
        }

        throw (
            "Add-AppxPackage returned without an error, but the package "
            + "could not be found for the current user after waiting 5 seconds."
        )
    }

    Write-Log -Text (
        "Registered package: "
        + $RegisteredPackage.PackageFullName
    )

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
