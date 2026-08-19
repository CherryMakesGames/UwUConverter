$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir
$buildDir = Join-Path $root "build-modern-shell"
$distDir = Join-Path $root "dist-modern-shell"
$generatedDir = Join-Path $scriptDir "generated"
$packageLayout = Join-Path $generatedDir "package"

function Find-WindowsSdkTool([string]$Name) {
    $kitsRoot = Join-Path ${env:ProgramFiles(x86)} "Windows Kits\10\bin"

    $candidate = Get-ChildItem `
        -Path (Join-Path $kitsRoot "*\x64\$Name") `
        -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        Select-Object -First 1

    if (!$candidate) {
        throw "$Name was not found in the Windows SDK."
    }

    return $candidate.FullName
}

Push-Location $root
try {
    python ".\windows_modern_shell\generate_actions.py"
    python ".\windows_modern_shell\generate_package_manifest.py"

    Remove-Item -Recurse -Force $buildDir -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force $distDir -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force $distDir | Out-Null

    cmake -S $scriptDir -B $buildDir -A x64
    cmake --build $buildDir --config Release

    $dll = Join-Path $buildDir "Release\UwUConverterShell.dll"
    if (!(Test-Path $dll)) {
        throw "Modern shell DLL was not built: $dll"
    }

    Copy-Item $dll (Join-Path $distDir "UwUConverterShell.dll") -Force

    $makeAppx = Find-WindowsSdkTool "makeappx.exe"
    $signTool = Find-WindowsSdkTool "signtool.exe"
    $package = Join-Path $distDir "UwUConverterShell.msix"

    & $makeAppx pack /o /d $packageLayout /nv /p $package
    if ($LASTEXITCODE -ne 0) {
        throw "MakeAppx failed with exit code $LASTEXITCODE"
    }

    $pfxPath = $env:UWUCONVERTER_MSIX_PFX_PATH
    $pfxPassword = $env:UWUCONVERTER_MSIX_PFX_PASSWORD
    $publisher = $env:UWUCONVERTER_MSIX_PUBLISHER
    $createdDevelopmentCertificate = $false

    if (!$publisher) {
        $publisher = "CN=UwUConverter Shell Extension"
    }

    if ($pfxPath) {
        if (!(Test-Path $pfxPath)) {
            throw "UWUCONVERTER_MSIX_PFX_PATH does not exist: $pfxPath"
        }

        $certificate = Get-PfxCertificate -FilePath $pfxPath
        $signingPfx = $pfxPath
    }
    else {
        $createdDevelopmentCertificate = $true
        $plainPassword = [guid]::NewGuid().ToString("N")
        $securePassword = ConvertTo-SecureString $plainPassword -AsPlainText -Force
        $signingPfx = Join-Path $distDir "UwUConverterShell.dev.pfx"
        $pfxPassword = $plainPassword

        $certificate = New-SelfSignedCertificate `
            -Type CodeSigningCert `
            -Subject $publisher `
            -FriendlyName "UwUConverter shell development certificate" `
            -CertStoreLocation "Cert:\CurrentUser\My" `
            -KeyExportPolicy Exportable `
            -NotAfter (Get-Date).AddYears(2)

        Export-PfxCertificate `
            -Cert $certificate `
            -FilePath $signingPfx `
            -Password $securePassword |
            Out-Null
    }

    $cerPath = Join-Path $distDir "UwUConverterShell.cer"
    Export-Certificate -Cert $certificate -FilePath $cerPath -Force | Out-Null

    $signArgs = @(
        "sign",
        "/fd", "SHA256",
        "/f", $signingPfx
    )

    if ($pfxPassword) {
        $signArgs += @("/p", $pfxPassword)
    }

    $signArgs += $package

    & $signTool @signArgs
    if ($LASTEXITCODE -ne 0) {
        throw "SignTool failed with exit code $LASTEXITCODE"
    }

    if ($createdDevelopmentCertificate) {
        Remove-Item $signingPfx -Force -ErrorAction SilentlyContinue
        Remove-Item ("Cert:\CurrentUser\My\" + $certificate.Thumbprint) -Force -ErrorAction SilentlyContinue
    }

    Write-Host "Modern shell build complete:"
    Write-Host "  $distDir\UwUConverterShell.dll"
    Write-Host "  $distDir\UwUConverterShell.msix"
    Write-Host "  $distDir\UwUConverterShell.cer"
}
finally {
    Pop-Location
}
