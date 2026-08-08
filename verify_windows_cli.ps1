$root = Join-Path $env:LOCALAPPDATA "Programs\UwUConverter"
$cli = Join-Path $root "cli\UwUConverter.exe"
$cliDir = Join-Path $root "cli"

Write-Host "CLI executable:" $cli
Write-Host "Exists:" (Test-Path $cli)

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
Write-Host "CLI folder in User PATH:" (($userPath -split ";") -contains $cliDir)

if (Test-Path $cli) {
    & $cli --version
}
