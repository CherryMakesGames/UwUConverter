@echo off
setlocal
cd /d "%~dp0"

rem UwUConverter 3.2: full local Windows build, matching GitHub Actions.
python -m pip install -r requirements.txt || exit /b 1
python -m pip install pyinstaller || exit /b 1

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist dist-cli rmdir /s /q dist-cli
if exist dist-browser-host rmdir /s /q dist-browser-host
if exist dist-modern-shell rmdir /s /q dist-modern-shell

python windows_modern_shell\generate_package_manifest.py || exit /b 1
python -m PyInstaller --clean --noconfirm --onedir --windowed --name UwUConverter --icon UwUConverter.ico --manifest windows_modern_shell\generated\UwUConverter.exe.manifest --add-data "UwUConverter.ico;." Converter.py || exit /b 1
python -m PyInstaller --clean --noconfirm --onefile --windowed --name UwUConverterBatch --icon UwUConverter.ico BatchLauncher.py || exit /b 1
python -m PyInstaller --clean --noconfirm --onefile --name UwUConverter --distpath dist-cli cli.py || exit /b 1
python -m PyInstaller --clean --noconfirm --onefile --windowed --name UwUConverterUpdater --icon UwUConverter.ico updater.py || exit /b 1
python -m PyInstaller --clean --noconfirm --onefile --name UwUConverterBrowserHost --distpath dist-browser-host browser_native_host.py || exit /b 1

python build_browser_extensions.py || exit /b 1
python -m unittest discover -s tests -v || exit /b 1

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File windows_modern_shell\build_modern_shell.ps1
if errorlevel 1 exit /b %errorlevel%

if not exist dist\UwUConverter\cli mkdir dist\UwUConverter\cli
copy /y dist\UwUConverterBatch.exe dist\UwUConverter\UwUConverterBatch.exe >nul || exit /b 1
copy /y dist-cli\UwUConverter.exe dist\UwUConverter\cli\UwUConverter.exe >nul || exit /b 1
copy /y dist\UwUConverterUpdater.exe dist\UwUConverter\UwUConverterUpdater.exe >nul || exit /b 1
copy /y dist-browser-host\UwUConverterBrowserHost.exe dist\UwUConverter\UwUConverterBrowserHost.exe >nul || exit /b 1
xcopy /e /i /y browser_extension\chromium dist\UwUConverter\browser-extension\chromium >nul || exit /b 1
xcopy /e /i /y browser_extension\firefox dist\UwUConverter\browser-extension\firefox >nul || exit /b 1
if not exist dist\UwUConverter\modern-shell mkdir dist\UwUConverter\modern-shell
copy /y dist-modern-shell\UwUConverterShell.dll dist\UwUConverter\modern-shell\UwUConverterShell.dll >nul || exit /b 1
copy /y dist-modern-shell\UwUConverterShell.msix dist\UwUConverter\modern-shell\UwUConverterShell.msix >nul || exit /b 1
copy /y dist-modern-shell\UwUConverterShell.cer dist\UwUConverter\modern-shell\UwUConverterShell.cer >nul || exit /b 1
copy /y windows_modern_shell\register_shell.ps1 dist\UwUConverter\modern-shell\register_shell.ps1 >nul || exit /b 1
copy /y windows_modern_shell\unregister_shell.ps1 dist\UwUConverter\modern-shell\unregister_shell.ps1 >nul || exit /b 1

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ISCC%" (
    "%ISCC%" installer.iss || exit /b 1
    echo Installer built in installer-output\
) else (
    echo Inno Setup was not found. Portable build is complete in dist\UwUConverter.
    echo Install Inno Setup 6 and compile installer.iss to create the Setup EXE.
)
echo UwUConverter 3.2 build complete.
exit /b 0
