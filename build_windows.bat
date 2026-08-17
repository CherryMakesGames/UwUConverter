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
if exist dist-browser-setup rmdir /s /q dist-browser-setup

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
echo Building browser installation helper...
python -m PyInstaller --clean --noconfirm --onefile --windowed --name UwUConverterBrowserSetup --icon UwUConverter.ico --distpath dist-browser-setup browser_setup.py
if errorlevel 1 exit /b %errorlevel%

if not exist "dist-browser-setup\UwUConverterBrowserSetup.exe" (
  echo ERROR: PyInstaller did not create dist-browser-setup\UwUConverterBrowserSetup.exe
  exit /b 1
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

copy /y ^
  "dist-browser-setup\UwUConverterBrowserSetup.exe" ^
  "dist\UwUConverter\UwUConverterBrowserSetup.exe"
if errorlevel 1 exit /b %errorlevel%

if exist "dist\UwUConverter\browser-extension" rmdir /s /q "dist\UwUConverter\browser-extension"
mkdir "dist\UwUConverter\browser-extension"
xcopy /e /i /y "browser_extension\chromium" "dist\UwUConverter\browser-extension\chromium" >nul
if errorlevel 1 exit /b %errorlevel%
xcopy /e /i /y "browser_extension\firefox" "dist\UwUConverter\browser-extension\firefox" >nul
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
echo   Browser setup: dist\UwUConverter\UwUConverterBrowserSetup.exe
echo   Chromium extension: browser_extension\dist\UwUConverter-Chromium.zip
echo   Firefox extension: browser_extension\dist\UwUConverter-Firefox.zip
echo.
echo The installer adds ONLY the cli folder to PATH.
pause
