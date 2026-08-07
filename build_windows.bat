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

echo.
echo Building windowless main executable...
python -m PyInstaller --clean --noconfirm UwUConverter.spec
if errorlevel 1 exit /b %errorlevel%

echo.
echo Building windowless batch GUI...
python -m PyInstaller --clean --noconfirm UwUConverterBatch.spec
if errorlevel 1 exit /b %errorlevel%

echo.
echo Copying batch GUI beside main executable...
copy /y "dist\UwUConverterBatch.exe" "dist\UwUConverter\UwUConverterBatch.exe"
if errorlevel 1 exit /b %errorlevel%

echo.
echo Verifying files...
if not exist "dist\UwUConverter\UwUConverter.exe" (
    echo ERROR: UwUConverter.exe was not created.
    exit /b 1
)

if not exist "dist\UwUConverter\UwUConverterBatch.exe" (
    echo ERROR: UwUConverterBatch.exe was not created.
    exit /b 1
)

echo.
echo Build complete:
echo dist\UwUConverter\UwUConverter.exe
echo dist\UwUConverter\UwUConverterBatch.exe
echo.
echo Both executables use the Windows GUI subsystem and do not create a console window.
pause
