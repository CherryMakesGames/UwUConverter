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
python -m PyInstaller --clean --noconfirm UwUConverterUpdater.spec
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

echo.
echo Build complete:
echo   GUI: dist\UwUConverter\UwUConverter.exe
echo   Batch GUI: dist\UwUConverter\UwUConverterBatch.exe
echo   CLI: dist\UwUConverter\cli\UwUConverter.exe
echo   Updater: dist\UwUConverter\UwUConverterUpdater.exe
echo.
echo The installer adds ONLY the cli folder to PATH.
pause
