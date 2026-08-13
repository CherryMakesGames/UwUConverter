# UwUConverter

[![Download UwUConverter](https://img.shields.io/sourceforge/dt/uwuconverter.svg)](https://sourceforge.net/projects/uwuconverter/files/latest/download)

![nya~](./Readme%20Images/banner.png)

UwUConverter is a local file conversion and archive utility written in Python. It supports right-click conversion, graphical batch conversion, compression, archive management, an installable command-line interface, and automatic updates.

The project currently supports Windows and experimental Linux integration.

## Features

- Right-click file conversion
- Right-click folder batch conversion supporting even millions of files
- Installable CLI command: `UwUConverter`
- Video conversion
- Audio conversion
- Audio extraction from video
- Image conversion
- Document conversion
- Spreadsheet conversion
- 3D model conversion
- Video compression
- Image compression
- 7-Zip-backed archive creation and extraction
- Archive right-click extraction menus
- Automatic application updates
- Windows File Explorer integration
- KDE Dolphin integration
- Nautilus integration
- Nemo integration
- Caja integration
- Built-in feature verification script

![Right Click Me Senpai~](Readme%20Images/Screenshot%202026-08-04%20155443.png)

![Fill Me Up With All The Batch Conversions mgh](Readme%20Images/Screenshot%202026-08-07%20133445.png)

[![Download UwUConverter](https://a.fsdn.com/con/app/sf-download-button)](https://sourceforge.net/projects/uwuconverter/files/latest/download)

# Supported Formats

## Video

Input:

```text
MP4
MKV
MOV
AVI
WEBM
```

Video output:

```text
MP4
MKV
MOV
AVI
WEBM
```

Audio extraction:

```text
MP3
WAV
FLAC
OGG
OPUS
```

## Audio

Input and output:

```text
MP3
WAV
FLAC
OGG
OPUS
```

## Images

Input:

```text
PNG
JPG
JPEG
WEBP
ICO
TIF
TIFF
RAW
```

Output:

```text
PNG
JPG
JPEG
WEBP
ICO
TIF
TIFF
PDF
```

RAW is input-only.

TIF and TIFF are both supported as normal image inputs and outputs.

## 3D Models

Input and output:

```text
OBJ
STL
PLY
GLB
```

3D model conversion uses `trimesh`.

OBJ and GLB can keep multiple scene objects. STL and PLY are exported as a single mesh, so multiple mesh objects are merged during conversion.

Format capabilities differ, so materials, textures, hierarchy, animations, cameras, lights, and other scene data may be lost when converting to simpler formats such as STL or PLY.

`.blend` conversion is not currently implemented.

## Documents

Input:

```text
PDF
DOCX
ODT
TXT
```

Output:

```text
PDF
DOCX
ODT
TXT
```

PDF to DOCX uses `pdf2docx`.

Other document conversions mainly preserve text rather than exact layout.

## Spreadsheets

Input:

```text
XLSX
XLS
XLSB
XLSM
ODS
CSV
TSV
```

Output:

```text
PDF
XLSX
XLS
ODS
CSV
TSV
```

XLSB and XLSM are currently input-only.

Spreadsheet conversion focuses mainly on cell values. Complex workbook features such as VBA, charts, pivot tables, formatting, and conditional formatting may not survive conversion.

# Right-Click Conversion

## Windows

Right-click a supported file and select:

```text
Convert With UwUConverter ^-^
```

The submenu exposes the conversions supported for that file type.

Single-file GUI conversions launch without opening a Command Prompt window.

Errors are shown in a message box instead.

Windows context menus are stored under the current user's registry keys rather than requiring system-wide registration.

## KDE Dolphin

Dolphin service menus are installed under:

```text
~/.local/share/kio/servicemenus/
```

UwUConverter creates service menus based on MIME types.

The installer cleans old UwUConverter service-menu entries before regenerating them to avoid stale or duplicate actions.

After changing menu integration manually, refreshing KDE's service cache can help:

```bash
kbuildsycoca6
dolphin --quit
dolphin &
```

# Batch Converter

Right-click a folder to open the graphical batch converter.

The batch GUI contains:

- Category selector
- Output mode selector
- Output format selector
- Folder scanning progress
- Conversion progress bar
- Converted/skipped/failed counters
- Current filename
- Cancel button
- Optional log checkbox

Conversion runs on a worker thread so the GUI remains responsive.

## Batch Categories

```text
Images
Video
Audio
Documents
Spreadsheets
3D Models
```

## Batch Output Modes

### Create a new folder

This is the default mode.

The converted folder is created beside the original folder.

Example:

```text
Pictures/
Pictures - Converted to WEBP/
```

### Place beside originals

Converted files are saved in the same folder as the source files.

Example:

```text
Pictures/
├── image01.png
├── image01.webp
├── image02.jpg
└── image02.webp
```

### Replace originals

The source is removed only after the converted file has been created successfully and verified to be non-empty.

Temporary files are created first and moved into place only after conversion succeeds.

Failed conversions leave the source untouched.

## Batch Logging

The GUI contains:

```text
[ ] Create log file in the source folder
```

Logging is disabled by default.

When enabled, UwUConverter creates:

```text
UwUConverter-batch-YYYYMMDD-HHMMSS.log
```

The log includes:

- skipped files
- failed files
- tracebacks
- totals
- elapsed time

## Large Folder Support

Batch conversion is designed to handle very large folders without keeping every path in memory.

The converter performs two streamed passes with `os.scandir()`:

1. Count matching files for progress reporting.
2. Convert matching files one at a time.

This keeps memory usage relatively stable even with folders containing tens of thousands of files.

Batch conversion is currently non-recursive.

# Archive Management

UwUConverter includes a 7-Zip-backed archive manager.

## Archive Creation

Archive creation currently supports:

```text
7Z
ZIP
TAR
GZIP / GZ
BZIP2 / BZ2
XZ
WIM
```

## Archive Extraction, Listing, and Testing

Extraction, listing, and integrity testing additionally support:

```text
RAR
CAB
ISO
ARJ
LZH
LZMA
RPM
DMG
XAR
```

RAR is extraction-only because 7-Zip does not create RAR archives.

## Archive CLI

Create an archive:

```powershell
UwUConverter archive create archive.7z ".\Folder"
UwUConverter archive create archive.zip ".\Folder" --level 9
```

Create a password-protected 7Z archive:

```powershell
UwUConverter archive create private.7z ".\Folder" --password password123 --encrypt-headers
```

Extract into an archive-named folder:

```powershell
UwUConverter archive extract archive.rar
```

Extract directly beside the archive:

```powershell
UwUConverter archive extract archive.rar --here
```

Delete the source archive only after successful extraction:

```powershell
UwUConverter archive extract archive.rar --delete-source
UwUConverter archive extract archive.rar --here --delete-source
```

List archive contents:

```powershell
UwUConverter archive list archive.7z
```

Test archive integrity:

```powershell
UwUConverter archive test archive.rar
```

## Archive Right-Click Menu

Supported archives get an extraction submenu.

```text
Extract With UwUConverter ^-^
├── Extract Here
├── Extract to Archive-Named Folder
├── Extract Here and Delete Archive
└── Extract to Archive-Named Folder and Delete Archive
```

The delete variants remove the source archive only after 7-Zip reports a successful extraction.

This menu is implemented for Windows File Explorer and KDE Dolphin.

## Automatic 7-Zip Setup

UwUConverter searches for existing 7-Zip installations first.

On Windows it checks normal PATH and Program Files locations. If 7-Zip is missing, UwUConverter can download and install the Windows 7-Zip package automatically.

On Linux it prefers a native `7zz` executable. If no usable 7-Zip command exists, UwUConverter can download a private copy into the user's UwUConverter data directory instead of requiring a system-wide installation.

The Linux archive launcher cleans PyInstaller-specific library environment variables before starting external 7-Zip/system processes. This prevents bundled libraries from leaking into `/bin/sh` or distro tools.

# Compression

UwUConverter supports image and video compression.

## GUI Compression Presets

The right-click GUI exposes:

```text
Lossless Optimize
Compress By 25%
Compress By 50%
Compress By 75%
```

The percentage represents the requested file-size reduction.

Example:

```text
25% reduction -> target roughly 75% of original size
50% reduction -> target roughly 50% of original size
75% reduction -> target roughly 25% of original size
```

These are targets rather than exact guarantees.

## CLI Compression

The CLI accepts any integer from 1 to 99:

```powershell
UwUConverter compress ".\video.mp4" --percent 40
UwUConverter compress ".\video.mp4" --percent 63
UwUConverter compress ".\image.webp" --percent 20
```

Lossless:

```powershell
UwUConverter compress ".\video.mp4" --lossless
UwUConverter compress ".\image.webp" --lossless
```

# Command-Line Interface

UwUConverter installs a normal console command:

```text
UwUConverter
```

The CLI supports:

- direct conversion
- compression
- batch conversion
- archive operations
- update checks
- menu installation
- menu removal
- format listing
- debug tracebacks

## Help

```powershell
UwUConverter --help
UwUConverter --version
UwUConverter formats
```

## Convert a File

```powershell
UwUConverter convert ".\photo.tif" --to webp
UwUConverter convert ".\video.mkv" --to mp4
UwUConverter convert ".\video.mp4" --to opus
UwUConverter convert ".\report.pdf" --to docx
UwUConverter convert ".\sheet.xlsx" --to csv
UwUConverter convert ".\model.obj" --to glb
```

Short format flag:

```powershell
UwUConverter convert ".\photo.png" -t webp
```

Exact output path:

```powershell
UwUConverter convert ".\photo.tif" -t png -o ".\converted.png"
```

Output directory:

```powershell
UwUConverter convert ".\photo.tif" -t webp --output-dir ".\converted"
```

Add a suffix:

```powershell
UwUConverter convert ".\photo.tif" -t webp --suffix "_small"
```

Overwrite an existing output:

```powershell
UwUConverter convert ".\photo.tif" -t webp --force
```

Delete the source after successful conversion:

```powershell
UwUConverter convert ".\photo.tif" -t webp --delete-source
```

## CLI Batch Conversion

Create a sibling output folder:

```powershell
UwUConverter batch ".\Pictures" -c image -t webp -m folder
```

Place outputs beside originals:

```powershell
UwUConverter batch ".\Pictures" -c image -t webp -m beside
```

Replace originals:

```powershell
UwUConverter batch ".\Pictures" -c image -t webp -m replace
```

Extract OPUS audio from matching videos:

```powershell
UwUConverter batch ".\Videos" -c video -t opus -m folder
```

Convert 3D models:

```powershell
UwUConverter batch ".\Models" -c model -t glb -m folder
```

Create a log:

```powershell
UwUConverter batch ".\Pictures" -c image -t webp --log
```

Quiet mode:

```powershell
UwUConverter batch ".\Pictures" -c image -t webp --quiet
```

## CLI Debug Mode

By default, CLI failures print a concise error.

For a traceback:

```powershell
UwUConverter --debug convert ".\broken.mkv" --to mp4
```

Ctrl+C exits with:

```text
Cancelled.
```

and exit code `130`.

## CLI Startup

Converters are loaded lazily.

For example, an image or video command does not load the PDF conversion libraries at startup.

This avoids unrelated PyMuPDF/`fitz` warnings and reduces unnecessary startup work.

# Automatic Updates

UwUConverter includes a separate updater executable on Windows and Linux.

The updater checks the latest published GitHub Release for:

```text
CherryMakesGames/UwUConverter
```

Automatic checks are cached for 24 hours.

## Update Commands

Check for and offer to install an update:

```bash
UwUConverter update
```

Only check:

```bash
UwUConverter update --check-only
```

Install without asking:

```bash
UwUConverter update --yes
```

## Windows Updater

The Windows installer installs:

```text
UwUConverterUpdater.exe
```

and registers it in the current user's startup entries.

The updater downloads the Windows installer asset from the latest release and starts Inno Setup after approval.

The preferred release asset name is:

```text
UwUConverter-Setup.exe
```

The updater can also recognize an `.exe` whose name contains `UwUConverter` and either `setup` or `installer`.

## Linux Updater

The Linux build includes:

```text
UwUConverterUpdater
```

The installer creates:

```text
~/.config/autostart/uwuconverter-updater.desktop
```

The updater checks after desktop login while respecting the 24-hour check cache.

Linux release assets are expected as:

```text
UwUConverter-linux-x86_64.tar.gz
UwUConverter-linux-arm64.tar.gz
```

The updater selects the package matching the current machine architecture, downloads it, verifies the release asset SHA-256 digest when supplied, safely extracts it, and runs:

```text
install.sh --update
```

The updater uses a verified SSL context and searches common system CA certificate bundle locations. This is important for PyInstaller builds on distributions where Python/OpenSSL does not automatically discover the host CA store.

Certificate verification is not disabled.

## Versioning

The application version is stored in:

```text
version.py
```

For a release, update `APP_VERSION`, keep `MyAppVersion` in `installer.iss` synchronized, and publish a newer release tag such as:

```text
v0.12
```

# Windows Installation

The installer places UwUConverter under:

```text
%LOCALAPPDATA%\Programs\UwUConverter
```

The GUI executable is:

```text
%LOCALAPPDATA%\Programs\UwUConverter\UwUConverter.exe
```

The batch GUI executable is:

```text
%LOCALAPPDATA%\Programs\UwUConverter\UwUConverterBatch.exe
```

The updater executable is:

```text
%LOCALAPPDATA%\Programs\UwUConverter\UwUConverterUpdater.exe
```

The CLI executable is:

```text
%LOCALAPPDATA%\Programs\UwUConverter\cli\UwUConverter.exe
```

Only the `cli` directory is added to the current user's PATH.

This means:

```powershell
UwUConverter
```

runs the CLI rather than the GUI.

After installation, open a new PowerShell or Command Prompt window before testing the command because already-open terminals retain their previous PATH environment.

Test:

```powershell
UwUConverter --version
UwUConverter formats
UwUConverter update --check-only
```

## PowerShell Current-Directory Behavior

PowerShell does not automatically execute programs from the current directory by filename alone.

When testing an unpacked executable directly from the current directory, use:

```powershell
.\UwUConverter.exe --help
```

not:

```powershell
UwUConverter.exe --help
```

Once installed and added to PATH, use:

```powershell
UwUConverter --help
```

from any directory.

# Windows Build

The project uses separate GUI, batch GUI, CLI, and updater executables.

The GUI, batch GUI, and updater use the Windows GUI subsystem so they do not open terminal windows.

The CLI intentionally uses the console subsystem.

Build with:

```text
build_windows.bat
```

The final installation layout includes:

```text
UwUConverter/
├── UwUConverter.exe
├── UwUConverterBatch.exe
├── UwUConverterUpdater.exe
├── cli/
│   └── UwUConverter.exe
└── _internal/
```

Compile the installer with Inno Setup:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" ".\installer.iss"
```

The installer adds:

```text
%LOCALAPPDATA%\Programs\UwUConverter\cli
```

to the user's PATH.

It removes that PATH entry during uninstall.

# Linux Support

Linux integration depends on the file manager.

Current support:

| File manager | Support |
| --- | --- |
| Dolphin | Yes |
| Nautilus | Yes |
| Nemo | Yes |
| Caja | Yes |
| Thunar | Not yet |
| PCManFM / PCManFM-Qt | Not yet |

Hyprland itself is not a file manager. UwUConverter works under Hyprland when paired with a supported file manager such as Dolphin.

## Dolphin

Dolphin gets individual-file conversion service menus, archive extraction actions, and a folder batch-conversion action.

Service menus are installed under:

```text
~/.local/share/kio/servicemenus/
```

## Nautilus

Scripts are installed under:

```text
~/.local/share/nautilus/scripts/UwUConverter/
```

## Nemo

Scripts are installed under:

```text
~/.local/share/nemo/scripts/UwUConverter/
```

## Caja

Scripts are installed under:

```text
~/.config/caja/scripts/UwUConverter/
```

## Linux Menu Cleanup

Installation performs cleanup before recreating menu entries.

This removes stale UwUConverter-generated integration files from previous versions.

Manual cleanup:

```bash
python3 cleanup_linux_menus.py
```

Uninstall menu integration:

```bash
python3 Converter.py --uninstall
```

For Dolphin, check remaining entries with:

```bash
find ~/.local/share/kio/servicemenus \
  -maxdepth 1 \
  -iname '*uwuconverter*' \
  -print
```

After uninstalling, this should return nothing.

# Linux Installation

The Linux installer stores the application under:

```text
~/.local/share/UwUConverter
```

and creates the CLI command:

```text
~/.local/bin/UwUConverter
```

It also installs the updater autostart entry.

Install:

```bash
chmod +x install.sh
./install.sh
```

Update an existing installation from an extracted release:

```bash
./install.sh --update
```

If `~/.local/bin` is not already in PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then:

```bash
UwUConverter --help
UwUConverter convert "./photo.tif" --to webp
UwUConverter batch "./Pictures" -c image -t webp
UwUConverter update --check-only
```

# Linux Build

Build with:

```bash
./build_linux.sh
```

On Arch, CachyOS, and other PEP 668 distributions, the build script prefers the project's `.venv`.

If no project venv exists, it creates an isolated build environment instead of trying to install packages into the system Python.

The build produces:

```text
UwUConverterGUI
UwUConverterBatch
UwUConverter
UwUConverterUpdater
```

and a release archive named according to the current architecture, for example:

```text
dist/UwUConverter-linux-x86_64.tar.gz
```

## Linux Build Size

The Linux package can currently be large.

A build around several hundred megabytes is possible because PyInstaller may bundle large Python and native dependencies such as:

- Python runtime
- PyAV and FFmpeg libraries
- Pillow
- rawpy and LibRaw
- pandas
- NumPy
- openpyxl
- xlrd
- xlwt
- pyxlsb
- reportlab
- pdf2docx
- PyMuPDF
- python-docx
- odfpy
- Tcl/Tk
- trimesh

Another major source of size is duplicate dependency bundles when the GUI, batch GUI, CLI, and updater are built independently.

Future packaging optimization should move toward a shared `onedir` dependency bundle so large libraries are stored once rather than duplicated between launchers.

The current priority is functionality and compatibility rather than minimum package size.

To inspect the largest files:

```bash
du -ah dist/UwUConverterGUI | sort -h | tail -40
```

To compare top-level build sizes:

```bash
du -sh dist/*
```

# Running From Source

Install dependencies in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Fish shell:

```fish
python3 -m venv .venv
source .venv/bin/activate.fish
pip install -r requirements.txt
```

## Windows

Install or refresh menus:

```powershell
python .\Converter.py
```

Run CLI:

```powershell
python .\cli.py --help
```

Open batch GUI directly:

```powershell
pythonw .\BatchLauncher.py ".\Pictures"
```

Uninstall menu integration:

```powershell
python .\Converter.py --uninstall
```

## Linux

Install Tkinter if required.

Arch / CachyOS:

```bash
sudo pacman -S tk
```

Ubuntu / Debian:

```bash
sudo apt install python3-tk
```

Fedora:

```bash
sudo dnf install python3-tkinter
```

Install or refresh integrations:

```bash
python3 Converter.py
```

Run CLI:

```bash
python3 cli.py --help
```

Open batch GUI:

```bash
python3 BatchLauncher.py "./Pictures"
```

Run the feature verifier:

```bash
python3 verify_features.py
```

# Feature Verification

The project includes:

```text
verify_features.py
```

It performs broad automated verification of conversion routing, archive handling, menus, batch modes, updater logic, Linux installation, and available converter backends.

The current verification run in the available Linux test environment reported:

```text
19 passed
1 skipped
0 failed
```

Runtime-tested successfully included:

- Python source syntax
- Linux shell-script syntax
- CLI parsing
- CLI format listing
- update-version comparison
- Windows/Linux release asset selection logic
- Linux update package extraction
- Linux updater install/autostart wiring
- isolated Linux install/uninstall
- KDE Dolphin file/folder/archive menu generation
- duplicate KDE service-menu prevention
- all three batch output modes
- batch logging
- PNG conversion to JPG/JPEG/WEBP/ICO/TIF/TIFF/PDF
- image lossless compression
- arbitrary-percentage image compression
- available TXT/DOCX/ODT/PDF document conversion paths
- available CSV/XLSX/ODS/TSV/PDF spreadsheet conversion paths
- OBJ to STL/PLY/GLB
- archive wrapper command routing
- Linux private `7zz` bootstrap using controlled fixtures
- Tkinter/batch GUI module imports

The test environment did not contain every optional/runtime dependency, so several platform-specific paths still require testing on the target machine.

In particular:

- real video/audio conversion and video compression require PyAV
- PDF to DOCX requires `pdf2docx`
- XLS output requires `xlwt`
- real archive extraction requires an actual 7-Zip runtime
- Windows registry integration and Inno Setup installation need a Windows environment

# Project Structure

```text
Converter.py
BatchLauncher.py
cli.py
updater.py
version.py
ssl_context.py
verify_features.py

batch_converter.py
batch_dialog.py
batch_menus.py

video_converter.py
audio_converter.py
image_converter.py
model_converter.py
archive_manager.py
media_compression.py
document_converter.py
spreadsheet_converter.py

file_types.py
platform_menu.py
make_key.py
linux_menu.py

cleanup_old_folder_menu.py
cleanup_linux_menus.py

UwUConverter.spec
UwUConverterBatch.spec
UwUConverterCLI.spec
UwUConverterUpdater.spec

build_windows.bat
build_linux.sh
installer.iss

install_linux.sh
uninstall_linux.sh

requirements.txt
UwUConverter.ico
```

# Main Modules

## `Converter.py`

Handles GUI-side routing, right-click actions, installation, and uninstall operations.

## `cli.py`

Provides the installable `UwUConverter` terminal command.

## `updater.py`

Checks GitHub Releases, selects platform-specific packages, verifies downloads, and starts the platform updater/install flow.

## `ssl_context.py`

Creates a verified TLS context and helps packaged Linux builds find the host system CA certificate store.

## `BatchLauncher.py`

Launches the graphical batch converter.

## `batch_dialog.py`

Provides the batch GUI, progress bar, counters, cancellation, and optional log checkbox.

## `batch_converter.py`

Streams folders, performs per-file conversion, tracks progress, handles safe replacement, and optionally writes logs.

## `model_converter.py`

Handles OBJ, STL, PLY, and GLB model conversion through `trimesh`.

## `archive_manager.py`

Wraps 7-Zip for archive creation, extraction, listing, integrity testing, automatic 7-Zip setup, and safe delete-after-extract behavior.

## `media_compression.py`

Handles image and video compression.

The module is named `media_compression.py` instead of `compression.py` to avoid shadowing Python 3.14's standard-library `compression` package.

## `file_types.py`

Defines single-file conversion actions.

## `platform_menu.py`

Selects Windows or Linux menu integration.

## `make_key.py`

Creates and removes Windows Registry menu entries.

## `linux_menu.py`

Creates and removes supported Linux file-manager integrations.

## `verify_features.py`

Runs broad automated project verification.

# Troubleshooting

## `UwUConverter` is not recognized on Windows

Check that the CLI exists:

```powershell
Test-Path "$env:LOCALAPPDATA\Programs\UwUConverter\cli\UwUConverter.exe"
```

Check the user PATH:

```powershell
[Environment]::GetEnvironmentVariable("Path", "User") -split ";" |
    Where-Object { $_ -like "*UwUConverter*" }
```

Expected entry:

```text
%LOCALAPPDATA%\Programs\UwUConverter\cli
```

Then close the current terminal and open a new one.

## PowerShell will not run `UwUConverter.exe` from the current folder

Use:

```powershell
.\UwUConverter.exe --help
```

rather than:

```powershell
UwUConverter.exe --help
```

unless the executable's directory is already in PATH.

## Batch path contains a stray quote

The CLI defensively trims invalid trailing double quotes from Windows paths before resolving them.

Example:

```powershell
UwUConverter batch -c image -t webp -m folder ".\random pics"
```

## Old or duplicate Dolphin actions remain

Refresh the integration:

```bash
python3 cleanup_linux_menus.py
python3 Converter.py
kbuildsycoca6
dolphin --quit
dolphin &
```

Inspect generated entries:

```bash
find ~/.local/share/kio/servicemenus \
  -maxdepth 1 \
  -iname '*uwuconverter*' \
  -print
```

## Linux updater reports `CERTIFICATE_VERIFY_FAILED`

UwUConverter uses `ssl_context.py` to locate common Linux CA certificate bundles while keeping certificate verification enabled.

Make sure the system CA certificates package is installed and rebuild/reinstall the packaged updater after updating the SSL helper.

On Arch/CachyOS the system CA packages should normally already be present as part of the base system.

## Linux archive extraction fails with a `/bin/sh` symbol lookup error

A failure similar to:

```text
/bin/sh: symbol lookup error: /bin/sh: undefined symbol: ...
```

can happen if a PyInstaller-packaged application passes its private `LD_LIBRARY_PATH` into a distro-provided shell wrapper.

The archive manager now restores or removes PyInstaller's library-path overrides before invoking external system tools and prefers `7zz` on Linux.

Rebuild and reinstall UwUConverter after updating `archive_manager.py`.

## 7-Zip is not found

UwUConverter attempts automatic setup when 7-Zip is missing.

On Windows it can download/install 7-Zip.

On Linux it can use or download a private `7zz` runtime.

You can still install 7-Zip manually through your operating system if preferred.

## Windows terminal still appears for GUI conversion

Make sure the installed GUI executable was rebuilt as a windowed PyInstaller application.

Changing Python source alone cannot change the subsystem of an already-built executable.

## Compression does not hit the exact requested size

Compression percentages are targets.

Codec limitations, minimum useful bitrates, container overhead, and existing compression can affect the final size.

## PDF warning appears on unrelated CLI commands

The CLI uses lazy imports to avoid loading document conversion dependencies when they are not needed.

If the warning still appears, confirm the installed CLI was rebuilt from the latest source.

## Python 3.14 fails with `compression._common`

Do not keep a local project file named:

```text
compression.py
```

Python 3.14 includes a standard-library package named `compression`.

UwUConverter uses:

```text
media_compression.py
```

instead.

# Development Status

UwUConverter is under active development.

Windows is currently the most tested platform.

Linux support is experimental and continues to receive testing across distributions, file managers, codecs, archive runtimes, SSL configurations, and packaging environments.

# License

UwUConverter is licensed under the MIT License.

See `LICENSE` for the full license text.
