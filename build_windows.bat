@echo off
setlocal
cd /d "%~dp0"

echo Installing dependencies...
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
echo Cleaning old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist dist-cli rmdir /s /q dist-cli
if exist dist-browser-host rmdir /s /q dist-browser-host
if exist build-modern-shell rmdir /s /q build-modern-shell
if exist dist-modern-shell rmdir /s /q dist-modern-shell

echo.
echo Generating Windows package identity metadata...
python windows_modern_shell\generate_package_manifest.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo Building windowless GUI executable...
python -m PyInstaller --clean --noconfirm UwUConverter.spec
if errorlevel 1 exit /b %errorlevel%

echo.
echo Building windowless batch GUI...
python -m PyInstaller --clean --noconfirm UwUConverterBatch.spec
if errorlevel 1 exit /b %errorlevel%

echo.
echo Building console CLI as UwUConverter.exe...
python -m PyInstaller --clean --noconfirm --distpath dist-cli UwUConverterCLI.spec
if errorlevel 1 exit /b %errorlevel%

echo.
echo Building windowless auto-updater...
python -m PyInstaller --clean --noconfirm --onefile --windowed --name UwUConverterUpdater --icon UwUConverter.ico updater.py
if errorlevel 1 exit /b %errorlevel%

if not exist "dist\UwUConverterUpdater.exe" (
  echo ERROR: PyInstaller did not create dist\UwUConverterUpdater.exe
  exit /b 1
)

for %%I in ("dist\UwUConverterUpdater.exe") do (
  if %%~zI LEQ 0 (
    echo ERROR: dist\UwUConverterUpdater.exe is empty
    exit /b 1
  )
)

echo.
echo Building browser native-messaging host...
python -m PyInstaller --clean --noconfirm --onefile --name UwUConverterBrowserHost --distpath dist-browser-host browser_native_host.py
if errorlevel 1 exit /b %errorlevel%

if not exist "dist-browser-host\UwUConverterBrowserHost.exe" (
  echo ERROR: PyInstaller did not create dist-browser-host\UwUConverterBrowserHost.exe
  exit /b 1
)

for %%I in ("dist-browser-host\UwUConverterBrowserHost.exe") do (
  if %%~zI LEQ 0 (
    echo ERROR: dist-browser-host\UwUConverterBrowserHost.exe is empty
    exit /b 1
  )
)


echo.
echo Building browser extension packages...
python build_browser_extensions.py
if errorlevel 1 exit /b %errorlevel%

if not exist "browser_extension\dist\UwUConverter-Chromium.zip" (
  echo ERROR: Chromium browser extension ZIP was not created
  exit /b 1
)

if not exist "browser_extension\dist\UwUConverter-Firefox.zip" (
  echo ERROR: Firefox browser extension ZIP was not created
  exit /b 1
)

echo.
echo Building Windows 11 modern context-menu extension...
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -File windows_modern_shell\build_modern_shell.ps1
if errorlevel 1 exit /b %errorlevel%

if not exist "dist-modern-shell\UwUConverterShell.dll" (
  echo ERROR: Modern shell DLL was not created
  exit /b 1
)

if not exist "dist-modern-shell\UwUConverterShell.msix" (
  echo ERROR: Modern shell identity package was not created
  exit /b 1
)

if not exist "dist-modern-shell\UwUConverterShell.cer" (
  echo ERROR: Modern shell certificate was not created
  exit /b 1
)

echo.
echo Creating final layout...
if not exist "dist\UwUConverter\cli" mkdir "dist\UwUConverter\cli"

copy /y ^
  "dist\UwUConverterBatch.exe" ^
  "dist\UwUConverter\UwUConverterBatch.exe"
if errorlevel 1 exit /b %errorlevel%

copy /y ^
  "dist-cli\UwUConverter.exe" ^
  "dist\UwUConverter\cli\UwUConverter.exe"
if errorlevel 1 exit /b %errorlevel%

copy /y ^
  "dist\UwUConverterUpdater.exe" ^
  "dist\UwUConverter\UwUConverterUpdater.exe"
if errorlevel 1 exit /b %errorlevel%

if not exist "dist\UwUConverter\UwUConverterUpdater.exe" (
  echo ERROR: Updater is missing from the final application layout
  exit /b 1
)

for %%I in ("dist\UwUConverter\UwUConverterUpdater.exe") do (
  if %%~zI LEQ 0 (
    echo ERROR: Final UwUConverterUpdater.exe is empty
    exit /b 1
  )
)

copy /y ^
  "dist-browser-host\UwUConverterBrowserHost.exe" ^
  "dist\UwUConverter\UwUConverterBrowserHost.exe"
if errorlevel 1 exit /b %errorlevel%


if exist "dist\UwUConverter\browser-extension" rmdir /s /q "dist\UwUConverter\browser-extension"
mkdir "dist\UwUConverter\browser-extension"
xcopy /e /i /y "browser_extension\chromium" "dist\UwUConverter\browser-extension\chromium" >nul
if errorlevel 1 exit /b %errorlevel%
xcopy /e /i /y "browser_extension\firefox" "dist\UwUConverter\browser-extension\firefox" >nul
if errorlevel 1 exit /b %errorlevel%

if exist "dist\UwUConverter\modern-shell" rmdir /s /q "dist\UwUConverter\modern-shell"
mkdir "dist\UwUConverter\modern-shell"
copy /y "dist-modern-shell\UwUConverterShell.dll" "dist\UwUConverter\modern-shell\UwUConverterShell.dll" >nul
if errorlevel 1 exit /b %errorlevel%
copy /y "dist-modern-shell\UwUConverterShell.msix" "dist\UwUConverter\modern-shell\UwUConverterShell.msix" >nul
if errorlevel 1 exit /b %errorlevel%
copy /y "dist-modern-shell\UwUConverterShell.cer" "dist\UwUConverter\modern-shell\UwUConverterShell.cer" >nul
if errorlevel 1 exit /b %errorlevel%
copy /y "windows_modern_shell\register_shell.ps1" "dist\UwUConverter\modern-shell\register_shell.ps1" >nul
if errorlevel 1 exit /b %errorlevel%
copy /y "windows_modern_shell\unregister_shell.ps1" "dist\UwUConverter\modern-shell\unregister_shell.ps1" >nul
if errorlevel 1 exit /b %errorlevel%

if not exist "dist\UwUConverter\UwUConverterBrowserHost.exe" (
  echo ERROR: Browser host is missing from the final application layout
  exit /b 1
)

for %%I in ("dist\UwUConverter\UwUConverterBrowserHost.exe") do (
  if %%~zI LEQ 0 (
    echo ERROR: Final UwUConverterBrowserHost.exe is empty
    exit /b 1
  )
)

echo.
echo Build complete:
echo   GUI: dist\UwUConverter\UwUConverter.exe
echo   Batch GUI: dist\UwUConverter\UwUConverterBatch.exe
echo   CLI: dist\UwUConverter\cli\UwUConverter.exe
echo   Updater: dist\UwUConverter\UwUConverterUpdater.exe
echo   Browser host: dist\UwUConverter\UwUConverterBrowserHost.exe
echo   Modern shell DLL: dist\UwUConverter\modern-shell\UwUConverterShell.dll
echo   Modern shell package: dist\UwUConverter\modern-shell\UwUConverterShell.msix
echo   Chromium extension: browser_extension\dist\UwUConverter-Chromium.zip
echo   Firefox extension: browser_extension\dist\UwUConverter-Firefox.zip
echo.
echo The installer adds ONLY the cli folder to PATH.
pause
