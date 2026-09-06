# UwUConverter

[![Download UwUConverter](https://img.shields.io/sourceforge/dt/uwuconverter.svg)](https://sourceforge.net/projects/uwuconverter/files/latest/download)

![nya~](./Readme%20Images/banner.png)

UwUConverter is a local file conversion, compression, and archive utility written in Python. It is built around fast right-click actions, but also includes graphical batch conversion, a WinRAR-style archive manager, browser image conversion, an installable CLI, and automatic updates.

Windows is the primary platform. Linux support is available for KDE Dolphin, Nautilus, Nemo, and Caja and is still considered experimental.

## Features

- Windows 11 modern File Explorer context menu
- Windows 10 / legacy Explorer fallback menu
- KDE Dolphin, Nautilus, Nemo, and Caja integration
- Multi-file right-click conversion
- Multi-selection `Compress Selection to ZIP...`
- Right-click folder batch conversion
- Graphical batch converter with progress and cancellation
- WinRAR-style graphical archive manager
- ZIP / 7Z / TAR / GZIP / BZIP2 / XZ / WIM archive creation
- RAR, CAB, ISO, ARJ, LZH, LZMA, RPM, DMG, and XAR extraction support
- Archive extraction, listing, integrity testing, adding, and deleting entries
- Video conversion
- Audio conversion
- Audio extraction from video
- Image conversion
- Camera RAW input
- TIFF / TIF support
- Document conversion
- Spreadsheet conversion
- 3D model conversion
- Image compression
- Video compression
- Installable CLI command: `UwUConverter`
- Browser right-click image conversion for Chromium-family browsers and Firefox
- Windows installer
- Linux graphical installer
- Automatic updates on Windows and Linux
- Automatic 7-Zip setup when required
- Optional batch logs
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

TIF and TIFF are supported as normal image inputs and outputs.

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

Materials, textures, hierarchy, animations, cameras, lights, and other scene data may be lost when converting to simpler formats.

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

XLSB and XLSM are input-only.

Spreadsheet conversion focuses mainly on cell values. Complex workbook features such as VBA, charts, pivot tables, formatting, and conditional formatting may not survive conversion.

# Windows File Explorer Integration

## Windows 11 modern menu

On Windows 11, UwUConverter uses a native `IExplorerCommand` shell extension so the app appears directly in the modern File Explorer context menu.

Example:

```text
UwUConverter >
    Image - Convert To WEBP
    Image - Compress By 50%
    Archive - Compress Selection to ZIP...
    Archive - Open Archive Manager
    ...
```

The shell extension only handles menu integration and selected paths. Conversion itself still runs through the normal UwUConverter executable.

Windows 11 uses the modern menu when registration succeeds. The old registry-based menu is not recreated at the same time, avoiding duplicate UwUConverter entries.

If modern registration fails, the classic menu remains available as a fallback.

## Windows 10 and classic fallback

The classic right-click menu uses registry verbs under the current user and does not normally require administrator privileges.

Depending on the file type, it exposes conversions, compression actions, archive actions, or the folder batch converter.

# Linux File Manager Integration

UwUConverter supports:

```text
KDE Dolphin
Nautilus
Nemo
Caja
```

## KDE Dolphin

Dolphin service menus are installed under:

```text
~/.local/share/kio/servicemenus/
```

UwUConverter generates MIME-aware conversion menus and also provides universal multi-selection actions where required.

After changing menu integration manually:

```bash
kbuildsycoca6
dolphin --quit
dolphin &
```

## Nautilus, Nemo, and Caja

UwUConverter installs script-based actions for supported operations, including archive management and multi-selection ZIP creation.

# Multi-Select Conversion

UwUConverter supports converting multiple selected files from the right-click menu.

Example selection:

```text
image1.png
image2.png
video.mp4
```

Choosing an image conversion processes compatible image files and skips incompatible files. Choosing a video action does the same for supported video files.

Mixed selections are therefore safe to use with the same menu.

Archive extraction actions also support multiple selected archives.

# Compress Multiple Selected Items to ZIP

Select one or more files or folders and choose:

```text
Compress Selection to ZIP...
```

One Save As dialog is shown for the entire selection.

For multiple selected items, the default archive name is:

```text
Archive.zip
```

For one selected item, the default name is based on that item.

When the selected items come from the same directory, UwUConverter passes relative names to 7-Zip so the archive contains normal paths instead of absolute filesystem paths.

This action is available through:

- Windows 11 modern File Explorer
- Windows classic File Explorer fallback
- KDE Dolphin
- Nautilus
- Nemo
- Caja

# Batch Converter

Right-click a folder to open the graphical batch converter.

The batch GUI contains:

- Category selector
- Output mode selector
- Output format selector
- Folder scanning progress
- Conversion progress bar
- Converted / skipped / failed counters
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

The converted folder is created beside the original folder.

```text
Pictures/
Pictures - Converted to WEBP/
```

### Place beside originals

Converted files are saved in the same folder as the source files.

```text
Pictures/
├── image01.png
├── image01.webp
├── image02.jpg
└── image02.webp
```

### Replace originals

The source is removed only after the converted file has been created successfully and verified to be non-empty.

Temporary output is created first and moved into place only after conversion succeeds.

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

The log includes skipped files, failed files, tracebacks, totals, and elapsed time.

## Large Folder Support

Batch conversion uses streamed directory scanning rather than loading every path into memory.

The current batch converter is non-recursive.

# Archive Management

UwUConverter uses 7-Zip as its archive backend.

## Graphical Archive Manager

Supported archives can be opened in the UwUConverter Archive Manager from the right-click menu.

The interface is intentionally similar to a classic WinRAR-style archive browser and includes:

```text
File   Commands   Tools   Help

[ Add ] [ Extract To ] [ Test ] [ Delete ] [ Info ] [ Up ] [ Refresh ]
```

The archive list displays:

```text
Name
Size
Packed
Type
Modified
CRC
```

The archive manager supports:

- Opening an archive
- Browsing folders inside an archive
- Multi-selecting archive entries
- Extracting selected entries
- Extracting the whole archive
- Adding files
- Adding folders
- Deleting selected entries when supported by the archive format
- Testing archive integrity
- Setting a password for encrypted extraction/testing
- Archive information
- Entry information
- Double-clicking a file to extract it temporarily and open it
- Creating new ZIP and 7Z archives

## Archive Creation

Creation currently supports:

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

## Right-Click Archive Menu

Supported archives expose actions such as:

```text
Open Archive Manager
Extract Here
Extract to Archive-Named Folder
Extract Here and Delete Archive
Extract to Archive-Named Folder and Delete Archive
```

The delete variants remove the source archive only after successful extraction.

## Archive CLI

Create:

```bash
UwUConverter archive create archive.7z "./Folder"
UwUConverter archive create archive.zip "./Folder" --level 9
```

Password-protected 7Z:

```bash
UwUConverter archive create private.7z "./Folder" --password password123 --encrypt-headers
```

Extract:

```bash
UwUConverter archive extract archive.rar
UwUConverter archive extract archive.rar --here
UwUConverter archive extract archive.rar --delete-source
```

List:

```bash
UwUConverter archive list archive.7z
```

Test:

```bash
UwUConverter archive test archive.rar
```

## Automatic 7-Zip Setup

UwUConverter first looks for an existing usable 7-Zip executable.

On Windows it checks normal PATH and Program Files locations.

On Linux it prefers a native `7zz`. If one is unavailable, UwUConverter can keep a private copy in the user's application data instead of requiring a system-wide package.

# Compression

UwUConverter supports image and video compression.

## GUI Presets

```text
Lossless Optimize
Compress By 25%
Compress By 50%
Compress By 75%
```

The percentage represents the requested reduction, not an exact guarantee.

## CLI

```bash
UwUConverter compress "./video.mp4" --percent 40
UwUConverter compress "./image.webp" --percent 20
```

# Browser Integration

UwUConverter includes browser extensions for Chromium-family browsers and Firefox.

Supported Chromium-family targets include:

```text
Google Chrome
Chromium
Microsoft Edge
Opera
Opera GX
Brave
Vivaldi
```

Firefox is supported separately.

Right-clicking an image in a supported browser exposes UwUConverter download/conversion actions such as:

```text
Download as PNG
Download as JPG
Download as JPEG
Download as WEBP
Download as ICO
Download as TIF
Download as TIFF
Download as PDF
```

The browser extension talks to the local `UwUConverterBrowserHost` through browser native messaging.

Current browser installation is assisted rather than silently forced by the application. Browsers intentionally restrict silent extension installation for normal desktop applications.

The installer detects supported browsers, lets the user choose which ones to set up, opens the browser extension-management page, and opens the bundled extension folder.

The same Chromium extension package is used for Chrome, Chromium, Edge, Opera, Opera GX, Brave, and Vivaldi.

# CLI

The packaged CLI command is:

```bash
UwUConverter
```

Examples:

```bash
UwUConverter --help
UwUConverter archive list archive.zip
UwUConverter compress image.png --percent 50
UwUConverter update --check-only
```

# Installation

## Windows

Download and run:

```text
UwUConverter-Setup.exe
```

The installer installs the main application, CLI, updater, browser native host, browser extension payloads, and File Explorer integrations.

The normal installation is per-user.

On Windows 11, the installer also registers the modern context-menu shell package.

## Linux graphical installer

Linux release archives contain:

```text
UwUConverterInstaller
```

Run:

```bash
./UwUConverterInstaller
```

The graphical installer can configure:

- Application installation
- CLI command
- File-manager integration
- Browser native-messaging support
- Browser extension setup
- Automatic updater

## Linux terminal installer

For terminal or headless installation:

```bash
./install.sh
```

The shell installer remains the backend used by the graphical installer.

# Automatic Updates

The updater checks the latest GitHub Release from:

```text
CherryMakesGames/UwUConverter
```

Automatic checks are cached so normal startup/login does not repeatedly hit the GitHub API.

## Windows updates

The Windows updater downloads the normal setup executable and launches the full Inno Setup installer.

Updates therefore use the same visible installer flow as a manual installation instead of silently replacing files.

## Linux updates

On a graphical Linux desktop, the updater downloads the matching release archive and opens `UwUConverterInstaller` in update mode.

Headless Linux falls back to:

```bash
install.sh --update
```

CLI update commands:

```bash
UwUConverter update
UwUConverter update --check-only
UwUConverter update --yes
```

# Building from Source

## Python dependencies

Install dependencies from:

```text
requirements.txt
```

or install the relevant Python packages manually.

The project uses libraries including:

```text
PyAV
Pillow
rawpy
pdf2docx
openpyxl
pandas
trimesh
PyInstaller
```

Some conversions also depend on external tools such as 7-Zip.

## Windows build

The Windows release uses:

- PyInstaller
- Inno Setup
- A native C++ Windows 11 shell extension
- A sparse MSIX package for modern File Explorer integration

The GitHub Actions Windows workflow builds the main GUI, batch converter, CLI, updater, browser host, browser extension ZIPs, modern shell DLL/package, and final Inno Setup installer.

## Linux build

Run:

```bash
chmod +x ./build_linux.sh
./build_linux.sh
```

The resulting package contains:

```text
UwUConverterGUI
UwUConverterBatch
UwUConverterUpdater
UwUConverterBrowserHost
UwUConverterInstaller
cli/UwUConverter
browser-extension/
install.sh
uninstall.sh
```

The GitHub Actions Linux workflow verifies the package contents and final tar archive before uploading the artifact.

# Development Notes

## Updating File Manager Menus

After changing supported file types or menu actions, regenerate the integration by running the application normally or reinstalling the current build.

Windows Explorer and KDE may cache menu registrations.

Windows Explorer can be restarted with:

```powershell
taskkill /f /im explorer.exe
start explorer.exe
```

KDE:

```bash
kbuildsycoca6
dolphin --quit
dolphin &
```

## Versions

Application version information lives in:

```text
version.py
```

Windows installer version information in `installer.iss` should be kept in sync with application releases.

# Known Limitations

- Linux integration is still experimental.
- Browser extensions currently use assisted installation until store-published versions are configured.
- Blob-backed browser images are not currently guaranteed to work.
- Images requiring authenticated browser cookies may fail to download through the native host.
- Not every codec can be remuxed into every video container.
- Some formats require transcoding and may be slow.
- VP8 encoding can be slow for large or high-resolution video.
- Subtitle, attachment, and data streams may be skipped.
- Camera RAW support depends on LibRaw compatibility.
- Office document conversion may not preserve complex layouts exactly.
- Spreadsheet conversion focuses primarily on cell values.
- XLSB / XLSM conversion can lose workbook-only features.
- Simplifying 3D model formats can lose materials, textures, hierarchy, animations, cameras, and lights.
- Batch conversion is currently non-recursive.
- Archive modification depends on what 7-Zip supports for the selected format.
- Some archive formats are extraction-only.
- Existing output files may be replaced or rejected depending on the operation.

# Troubleshooting

## Windows 11 menu does not appear

The modern menu is registered during installation.

If modern registration fails, UwUConverter falls back to the classic context menu.

Reinstalling the latest setup package refreshes both the package registration and fallback state.

## Two UwUConverter entries appear on Windows 11

Newer builds remove the old static registry verbs after the modern shell package has registered successfully.

Reinstall the latest setup package to clean stale menu registrations.

## Linux installer is missing from the package

A current Linux release should contain:

```text
UwUConverterInstaller
```

The GitHub Actions package verification checks this before publishing.

## Archive actions behave like folder actions on Windows

Modern builds classify folders using real filesystem attributes rather than Explorer's shell-folder flag. This prevents ZIP files from being mistaken for directories.

# Reporting Bugs

When reporting a conversion or integration problem, include:

- Operating system and version
- UwUConverter version
- Input extension
- Requested output/action
- Full error traceback or installer/update log
- Source audio/video codecs when relevant
- File manager or browser when the problem is integration-related

# License

UwUConverter is licensed under the MIT License.

You may use, copy, modify, distribute, sublicense, and sell copies of the software, provided that the original copyright and license notice are preserved.

The software is provided without warranty. See the `LICENSE` file for the complete license text.

# Development Status

UwUConverter is a learning project and is under active development. Some unusual files, codecs, camera RAW formats, archive formats, office documents, 3D models, browser integrations, and conversion combinations may not work correctly yet.
