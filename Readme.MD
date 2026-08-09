# UwUConverter
[![Download UwUConverter](https://img.shields.io/sourceforge/dt/uwuconverter.svg)](https://sourceforge.net/projects/uwuconverter/files/latest/download)
![nya~](./Readme%20Images/banner.png)

UwUConverter is a local file conversion utility written in Python. It supports right-click conversion, a graphical batch converter, and an installable command-line interface.

The project currently supports Windows and experimental Linux integration.

## Features
- Right-click file conversion
- Right-click folder batch conversion
- Installable CLI command: `UwUConverter`
- Video conversion
- Audio conversion
- Audio extraction from video
- Image conversion
- Camera RAW input
- Document conversion
- Spreadsheet conversion
- Video compression
- Image compression
- Safe batch replacement
- Large-folder batch processing
- Windows File Explorer integration
- Dolphin integration
- Nautilus integration
- Nemo integration
- Caja integration
- 7-zip cli bundled integration
- 3D model conversion
- 7-Zip archive creation, extraction, listing, and testing
- Archive right-click extraction menu on KDE/Dolphin

![Right Click Me Senpai~](Readme%20Images/Screenshot%202026-08-04%20155443.png)
![Fill Me Up With All The Batch Conversions mgh](Readme%20Images/Screenshot%202026-08-07%20133445.png)
[![Download UwUConverter](https://a.fsdn.com/con/app/sf-download-button)](https://sourceforge.net/projects/uwuconverter/files/latest/download)
## Supported Formats
### Video
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

### Audio
Input and output:

```text
MP3
WAV
FLAC
OGG
OPUS
```

### Images
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

### 3D Models

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

### Documents
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

### Spreadsheets
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
On Windows, right-click a supported file and select:

```text
Convert With UwUConverter ^-^
```

The menu exposes the conversion options supported for that file type.

Single-file conversions on Windows launch without opening a Command Prompt window.

Errors are shown in a message box instead.

# Batch Converter
Right-click a folder to open the batch converter.

The batch GUI contains:

- Category selector
- Output mode selector
- Output format selector
- Folder scanning progress
- Conversion progress bar

The conversion runs on a worker thread so the window remains responsive.

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

When disabled, no `.log` file is created.

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

UwUConverter includes a basic 7-Zip-backed archive CLI. On Windows, the installer checks for 7-Zip and attempts to install it automatically when it is missing.

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

Extraction, listing, and archive testing additionally support common formats such as:

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

Extract into an archive-named folder:

```powershell
UwUConverter archive extract archive.rar
```

Extract directly beside the archive:

```powershell
UwUConverter archive extract archive.rar --here
```

Delete the source archive only after a successful extraction:

```powershell
UwUConverter archive extract archive.rar --delete-source
UwUConverter archive extract archive.rar --here --delete-source
```

List or test an archive:

```powershell
UwUConverter archive list archive.7z
UwUConverter archive test archive.rar
```

## KDE / Dolphin Archive Menu

Supported archives get an `Extract With UwUConverter ^-^` submenu with:

- Extract Here
- Extract to Archive-Named Folder
- Extract Here and Delete Archive
- Extract to Archive-Named Folder and Delete Archive

The delete actions only remove the source archive after 7-Zip reports a successful extraction.

# Compression
UwUConverter supports image and video compression.

## GUI Compression Presets
The right-click GUI currently exposes:

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
The CLI is more flexible and accepts any integer from 1 to 99:

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

The CLI does not open the batch GUI.

It supports direct conversion, compression, batch conversion, archive operations, menu installation, and format listing.

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

Extract OPUS audio from all matching videos:

```powershell
UwUConverter batch ".\Videos" -c video -t opus -m folder
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

For example, image or video commands do not load the PDF conversion libraries at startup.

This avoids unrelated PyMuPDF/`fitz` warnings and improves CLI startup time.

# Windows Installation
The installer places the application under:

```text
%LOCALAPPDATA%\Programs\UwUConverter
```

The GUI executable is:

```text
%LOCALAPPDATA%\Programs\UwUConverter\UwUConverter.exe
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

runs the CLI instead of the GUI.

After installation, open a new PowerShell or Command Prompt window before testing the command because already-open terminals keep their previous PATH environment.

Test:

```powershell
UwUConverter --version
UwUConverter formats
```

## PowerShell Current-Directory Behavior
PowerShell does not automatically execute programs from the current directory by filename alone.

If you are testing an unpacked executable directly from the current directory, use:

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
The project uses separate GUI and CLI executables.

The GUI executables use the Windows GUI subsystem so they do not open terminal windows.

The CLI intentionally uses the console subsystem.

Build with:

```text
build_windows.bat
```

The final installation layout should include:

```text
UwUConverter/
├── UwUConverter.exe
├── UwUConverterBatch.exe
├── cli/
│   └── UwUConverter.exe
└── _internal/
```

Compile the installer with Inno Setup:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" ".\installer.iss"
```

The installer explicitly adds:

```text
%LOCALAPPDATA%\Programs\UwUConverter\cli
```

to the user's PATH.

It also removes that PATH entry during uninstall.

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

Hyprland itself is not a file manager. UwUConverter works under Hyprland when used with a supported file manager such as Dolphin.

## Dolphin
The current service menu is installed under:

```text
~/.local/share/kio/servicemenus/
```

The folder action opens the same batch GUI used on Windows.

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

Uninstall:

```bash
python3 Converter.py --uninstall
```

For Dolphin, check remaining entries with:

```bash
find ~/.local/share/kio/servicemenus \\
  -maxdepth 1 \\
  -iname '*uwuconverter*' \\
  -print
```

After uninstalling, this should return nothing.

# Linux CLI Installation
The Linux installer creates:

```text
~/.local/bin/UwUConverter
```

The application itself is stored under:

```text
~/.local/share/UwUConverter
```

Install:

```bash
chmod +x install.sh
./install.sh
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
```

# Linux Build Size
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

Another major source of size is duplicate dependency bundles when the GUI, batch GUI, and CLI are built independently.

Future packaging optimization should move toward a shared `onedir` dependency bundle so the runtime and large libraries are stored once rather than duplicated between launchers.

Removing pandas from the spreadsheet converter is another likely size reduction because pandas normally pulls in NumPy and other large dependencies.

The current priority is functionality and compatibility rather than minimum package size.

To inspect the largest files in a Linux build:

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

# Project Structure
```text
Converter.py
BatchLauncher.py
cli.py

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

build_windows.bat
build_linux.sh
installer.iss

install_linux.sh
uninstall_linux.sh

requirements.txt
UwUConverter.ico
```

# Main Modules
### `Converter.py`
Handles GUI-side routing, right-click actions, installation, and uninstall operations.

### `cli.py`
Provides the installable `UwUConverter` terminal command.

### `BatchLauncher.py`
Launches the graphical batch converter.

### `batch_dialog.py`
Provides the batch GUI, progress bar, counters, cancellation, and optional log checkbox.

### `batch_converter.py`
Streams folders, performs per-file conversion, tracks progress, handles safe replacement, and optionally writes logs.

### `model_converter.py`

Handles OBJ, STL, PLY, and GLB model conversion through `trimesh`.

### `archive_manager.py`

Wraps the 7-Zip CLI for archive creation, extraction, listing, testing, and safe delete-after-extract behavior.

### `file_types.py`
Defines single-file context-menu actions.

### `platform_menu.py`
Selects Windows or Linux menu integration.

### `make_key.py`
Creates and removes Windows Registry menu entries.

### `linux_menu.py`
Creates and removes supported Linux file-manager integrations.

### `media_compression.py`
Handles image and video compression.

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

## Batch path contains a stray quote
The CLI defensively trims invalid trailing double quotes from Windows paths before resolving them.

This command is valid:

```powershell
UwUConverter batch -c image -t webp -m folder ".\random pics"
```

## Old Dolphin actions remain
Run:

```bash
python3 cleanup_linux_menus.py
python3 Converter.py
```

Then restart Dolphin.

## Windows terminal still appears for GUI conversion
Make sure the installed GUI executable was rebuilt as a windowed PyInstaller application.

Changing the Python source alone cannot change the subsystem of an already-built executable.

## Compression does not hit the exact requested size
Compression percentages are targets.

Codec limitations, minimum useful bitrates, container overhead, and existing compression can affect the final size.

## PDF warning appears on unrelated CLI commands
The current CLI uses lazy imports specifically to avoid loading document conversion dependencies when they are not needed.

If the warning still appears, confirm that the installed CLI was rebuilt from the latest source.

# Development Status
UwUConverter is under active development.

Windows is currently the most tested platform.

Linux support is experimental and still needs broader testing across distributions, file managers, codecs, and package configurations.

# License
UwUConverter is licensed under the MIT License.

See `LICENSE` for the full license text.
