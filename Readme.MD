# UwUConverter

![nya~](./Readme%20Images/banner.png)

UwUConverter is a local file converter written in Python. It adds conversion and compression actions directly to the file manager's right-click menu, allowing files and folders to be processed without opening a separate application first.

The project supports Windows and experimental Linux integration for Dolphin, Nautilus, Nemo, and Caja.

## Usage Preview

![cOwOnvert Pwetty Pwease](./Readme%20Images/Screenshot%202026-08-04%20155327.png)
![cOwOmpress Pwease](./Readme%20Images/Screenshot%202026-08-04%20155443.png)

## Main Features

- Converts files directly from the right-click menu
- Supports video, audio, images, camera RAW files, documents, and spreadsheets
- Supports video and image compression
- Includes a graphical batch converter for folders
- Shows batch progress, counters, the current filename, and cancellation controls
- Handles very large folders without loading every path into memory
- Supports three batch output modes
- Makes detailed batch logs optional
- Uses hidden or windowed launchers so conversions do not open terminal windows
- Supports Windows File Explorer
- Supports KDE Plasma through Dolphin
- Supports GNOME through Nautilus
- Supports Cinnamon through Nemo
- Supports MATE through Caja
- Installs and removes its own file-manager integrations
- Uses separate modules for conversion, compression, batch processing, and platform integration

## Download

### Windows

Download the latest Windows installer from the GitHub Releases page:

```text
UwUConverter-Setup.exe
```

The installer places UwUConverter in a permanent application folder, installs the right-click menu entries, copies the application icon, and adds uninstall support.

### Linux

Linux releases are currently experimental and should be distributed as a compressed archive:

```text
UwUConverter-Linux-x64.tar.gz
```

Extract the archive and run the main executable once to install the file-manager integrations:

```bash
tar -xzf UwUConverter-Linux-x64.tar.gz
chmod +x UwUConverter/UwUConverter
chmod +x UwUConverter/UwUConverterBatch
./UwUConverter/UwUConverter
```

## Supported Formats

### Video Input

- MP4
- MKV
- MOV
- AVI
- WebM

Video output options:

- MP4
- MKV
- MOV
- AVI
- WebM

Audio extraction options:

- MP3
- WAV
- FLAC
- OGG
- OPUS

### Audio Input

- MP3
- WAV
- OGG
- FLAC
- OPUS

Audio output options:

- MP3
- WAV
- FLAC
- OGG
- OPUS

### Image Input

- PNG
- JPG
- JPEG
- WebP
- ICO
- RAW

Image output options:

- PNG
- JPG
- JPEG
- WebP
- ICO
- PDF

RAW is input-only. UwUConverter does not create camera RAW files.

RAW support depends on whether `rawpy` and LibRaw recognize the camera format.

### Document Input

- PDF
- DOCX
- ODT
- TXT

Document output options:

- PDF
- DOCX
- ODT
- TXT

PDF-to-DOCX conversion uses `pdf2docx`.

Other document conversions focus mainly on text content. Exact layout, images, tables, fonts, headers, footers, columns, spacing, and pagination may not be preserved.

Legacy `.doc` files are not currently supported.

### Spreadsheet Input

- XLSX
- XLS
- XLSB
- XLSM
- ODS
- CSV
- TSV

Spreadsheet output options:

- PDF
- XLSX
- XLS
- ODS
- CSV
- TSV

XLSB and XLSM are currently input-only.

Spreadsheet conversions focus on cell values. The following may be lost or changed:

- Formulas
- VBA macros
- Charts
- Pivot tables
- Cell styling
- Conditional formatting
- Workbook metadata
- Multiple sheets when exporting to CSV or TSV

## Single-File Conversion

Right-click a supported file and open:

```text
Convert With UwUConverter ^-^
```

Choose the required conversion or compression action.

The result is saved beside the source file.

Examples:

```text
video.mkv -> video.mp4
video.mp4 -> video.mp3
song.wav -> song.opus
photo.raw -> photo.png
document.docx -> document.pdf
spreadsheet.xlsx -> spreadsheet.csv
```

Single-file conversions launch without a terminal window on Windows.

When a conversion fails, UwUConverter displays an error window containing the traceback.

## Compression

UwUConverter provides four compression options for supported images and videos:

- Lossless Optimize
- Compress By 25%
- Compress By 50%
- Compress By 75%

The percentage describes the intended reduction from the original file size:

```text
Compress By 25% -> aims for about 75% of the original size
Compress By 50% -> aims for about 50% of the original size
Compress By 75% -> aims for about 25% of the original size
```

The result is a target rather than an exact guarantee.

Final size can vary because of:

- Source codec
- Existing compression
- Image contents
- Video duration
- Minimum practical bitrates
- Metadata
- Container overhead

Video percentage compression keeps the original file extension and container.

Lossless optimization may only save a small amount when the source is already efficiently encoded.

## Batch Converter

Right-click a folder and select the UwUConverter batch entry.

On Windows:

```text
Convert With UwUConverter ^-^
```

On Dolphin:

```text
Batch Convert With UwUConverter
```

On Nautilus, Nemo, and Caja, the launcher appears inside the file manager's `Scripts` submenu.

The batch window contains:

- Category
- Output mode
- Output format
- Create log checkbox
- Scanning progress
- Conversion progress bar
- Converted count
- Skipped count
- Failed count
- Current filename
- Cancel button

### Batch Categories

- Images
- Video
- Audio
- Documents
- Spreadsheets

The batch converter exposes every output format currently supported by the matching single-file converter.

### Batch Output Modes

#### Replace Originals

Successfully converted files replace their source files.

UwUConverter first converts to a temporary file. The source is only removed after the output exists and is not empty.

When the source and destination use the same extension, the temporary result atomically replaces the original.

Failed conversions leave the original file untouched.

#### Create a New Folder

A new sibling folder is created beside the selected source folder.

Example:

```text
Pictures/
Pictures - Converted to WEBP/
```

The converted files are placed in the new folder.

#### Place Beside Originals

Converted files are placed directly beside their source files.

Example:

```text
Pictures/
├── image01.png
├── image01.webp
├── image02.jpg
└── image02.webp
```

Existing destination files are skipped instead of overwritten.

### Optional Batch Logs

The batch window contains:

```text
[ ] Create log file in the source folder
```

The checkbox is disabled by default.

When disabled, UwUConverter does not create a log file in the source folder.

When enabled, it creates:

```text
UwUConverter-batch-YYYYMMDD-HHMMSS.log
```

The log includes:

- Skipped files
- Failed files
- Tracebacks
- Totals
- Elapsed time

### Large Folder Support

The batch converter is designed to work with extremely large folders, including folders containing around 100,000 files.

It uses two streaming passes:

1. Count matching files for the progress bar.
2. Convert matching files one at a time.

It does not build a list containing every file path.

The implementation uses:

- `os.scandir()` for streamed directory access
- Stable memory use
- Sequential conversion
- One active conversion at a time
- Per-file error handling
- Safe cancellation after the current file
- Temporary output files
- Atomic final replacement where supported
- Optional line-buffered logging

The current implementation processes files directly inside the selected folder. It does not recursively process nested folders.

A folder with 100,000 files can still take a long time to scan and convert, but memory use should remain relatively stable.

## Windows Support

### File Explorer Integration

Single-file menus are registered under:

```text
HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations
```

The folder batch command is registered under:

```text
HKEY_CURRENT_USER\Software\Classes\Directory\shell\UwUConverter
```

Administrator access should not normally be required because the entries are installed for the current user.

### Windows Installation Location

The installer normally places UwUConverter under:

```text
%LOCALAPPDATA%\Programs\UwUConverter
```

The context-menu icon is copied to:

```text
%LOCALAPPDATA%\UwUConverter\icon.ico
```

### No Terminal Windows

Source-mode context-menu actions use `pythonw.exe`.

Packaged releases should build both executables with PyInstaller's `--windowed` option:

```text
UwUConverter.exe
UwUConverterBatch.exe
```

The normal converter handles single-file actions and menu installation.

The batch executable opens the graphical folder converter and progress window.

## Linux Support

Linux integration depends on the file manager rather than only the desktop environment.

Current support:

| Desktop or setup | File manager | Integration |
|---|---|---|
| KDE Plasma | Dolphin | Service menu |
| Hyprland with Dolphin | Dolphin | Service menu |
| GNOME | Nautilus | Scripts submenu |
| Cinnamon | Nemo | Scripts submenu |
| MATE | Caja | Scripts submenu |
| Other desktop with a supported file manager | Dolphin, Nautilus, Nemo, or Caja | Supported |
| XFCE default setup | Thunar | Not currently integrated |
| LXQt default setup | PCManFM-Qt | Not currently integrated |

The converter can still be run manually on unsupported desktops.

### Dolphin

The batch GUI service menu is installed at:

```text
~/.local/share/kio/servicemenus/uwuconverter-batch-gui.desktop
```

Right-click a folder and select:

```text
Batch Convert With UwUConverter
```

### Nautilus

Scripts are installed under:

```text
~/.local/share/nautilus/scripts/UwUConverter/
```

### Nemo

Scripts are installed under:

```text
~/.local/share/nemo/scripts/UwUConverter/
```

### Caja

Scripts are installed under:

```text
~/.config/caja/scripts/UwUConverter/
```

### Linux Menu Cleanup

Every Linux installation begins by removing older UwUConverter-generated integrations.

This removes:

- Old nested Dolphin batch menus
- Old Dolphin conversion menus
- Older batch GUI service-menu files
- Old Nautilus scripts
- Old Nemo scripts
- Old Caja scripts

Only the current integration is recreated.

To clean the Linux menus manually:

```bash
python3 cleanup_linux_menus.py
```

To uninstall all current and older UwUConverter Linux menu entries:

```bash
python3 Converter.py --uninstall
```

Check remaining Dolphin entries:

```bash
find ~/.local/share/kio/servicemenus \
  -maxdepth 1 \
  -iname '*uwuconverter*' \
  -print
```

After uninstalling, the command should print nothing.

### Restarting Dolphin

When Dolphin does not refresh automatically:

```bash
kquitapp6 dolphin
dolphin &
```

Some installations may use:

```bash
dolphin --quit
dolphin &
```

## Running From Source

### Requirements

- Python 3.10 or newer
- Dependencies from `requirements.txt`
- Tkinter for the batch GUI

Install Python dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Windows

Install or refresh the context menus:

```powershell
python .\Converter.py
```

Run a conversion manually:

```powershell
python .\Converter.py "D:\Videos\example.mkv" "WEBM"
```

Open the batch GUI manually:

```powershell
pythonw .\BatchLauncher.py "D:\Pictures"
```

Remove the context-menu entries:

```powershell
python .\Converter.py --uninstall
```

Clean old folder-menu experiments:

```powershell
python .\cleanup_old_folder_menu.py
```

Restart Explorer:

```powershell
taskkill /f /im explorer.exe
start explorer.exe
```

### Linux

Some distributions package Tkinter separately.

Arch, CachyOS, and other Arch-based systems:

```bash
sudo pacman -S tk
```

Ubuntu and Debian-based systems:

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

Run a conversion manually:

```bash
python3 Converter.py "/home/user/Videos/example.mkv" "WEBM"
```

Open the batch GUI manually:

```bash
python3 BatchLauncher.py "/home/user/Pictures"
```

Remove integrations:

```bash
python3 Converter.py --uninstall
```

## Project Structure

```text
Converter.py
BatchLauncher.py
batch_converter.py
batch_dialog.py
batch_menus.py
platform_menu.py
make_key.py
linux_menu.py
cleanup_old_folder_menu.py
cleanup_linux_menus.py
file_types.py
video_converter.py
audio_converter.py
image_converter.py
compression.py
document_converter.py
spreadsheet_converter.py
requirements.txt
UwUConverter.ico
installer.iss
```

### Main Files

`Converter.py`

Routes single-file actions, compression actions, batch actions, installation, and uninstall operations.

`BatchLauncher.py`

Opens the graphical batch converter.

`batch_converter.py`

Streams folder contents, converts matching files, tracks progress, handles cancellation, and optionally writes logs.

`batch_dialog.py`

Provides the batch GUI and progress bar.

`batch_menus.py`

Contains batch categories and supported output formats.

`file_types.py`

Contains single-file extension menus and actions.

`platform_menu.py`

Selects Windows or Linux integration at runtime.

`make_key.py`

Creates and removes Windows Registry menu entries.

`linux_menu.py`

Creates and removes Dolphin, Nautilus, Nemo, and Caja integrations.

`video_converter.py`

Handles video containers and transcoding.

`audio_converter.py`

Handles audio conversion and audio extraction.

`image_converter.py`

Handles ordinary images and camera RAW input.

`compression.py`

Handles image and video compression.

`document_converter.py`

Handles document conversion.

`spreadsheet_converter.py`

Handles spreadsheet conversion.

## Building for Windows

Build the main executable as a windowed `onedir` application:

```powershell
pyinstaller --clean --noconfirm --onedir ^
  --windowed ^
  --name UwUConverter ^
  --icon UwUConverter.ico ^
  --add-data "UwUConverter.ico;." ^
  Converter.py
```

Build the batch GUI as a windowed single-file executable:

```powershell
pyinstaller --clean --noconfirm --onefile ^
  --windowed ^
  --name UwUConverterBatch ^
  --icon UwUConverter.ico ^
  BatchLauncher.py
```

Copy the batch executable into the main build folder:

```powershell
Copy-Item `
  .\dist\UwUConverterBatch.exe `
  .\dist\UwUConverter\UwUConverterBatch.exe
```

The final folder should contain:

```text
dist\UwUConverter\
├── UwUConverter.exe
├── UwUConverterBatch.exe
└── _internal\
```

Test menu installation:

```powershell
.\dist\UwUConverter\UwUConverter.exe
```

### Building the Installer

Compile `installer.iss` with Inno Setup 6.

The installer script should copy the complete PyInstaller folder:

```text
dist\UwUConverter\
```

The installer output is normally created under:

```text
installer-output\UwUConverter-Setup.exe
```

## Building for Linux

Linux executables must be built on Linux.

Build the main executable:

```bash
pyinstaller \
  --clean \
  --noconfirm \
  --onedir \
  --windowed \
  --name UwUConverter \
  --add-data "UwUConverter.ico:." \
  Converter.py
```

Build the batch GUI as a windowed single-file executable:

```bash
pyinstaller \
  --clean \
  --noconfirm \
  --onefile \
  --windowed \
  --name UwUConverterBatch \
  BatchLauncher.py
```

Copy it into the main build folder:

```bash
cp \
  dist/UwUConverterBatch \
  dist/UwUConverter/UwUConverterBatch
```

Make both launchers executable:

```bash
chmod +x dist/UwUConverter/UwUConverter
chmod +x dist/UwUConverter/UwUConverterBatch
```

Test menu installation:

```bash
./dist/UwUConverter/UwUConverter
```

Create the release archive:

```bash
cd dist
tar -czf UwUConverter-Linux-x64.tar.gz UwUConverter
```

A Linux build created on an older base distribution generally has a better chance of working on newer distributions.

Linux releases should remain marked experimental until tested across multiple distributions, file managers, and desktop environments.

## Updating File-Manager Menus

After changing `file_types.py`, `batch_menus.py`, or platform menu code, reinstall the integrations.

Windows:

```powershell
python .\Converter.py
```

Linux:

```bash
python3 Converter.py
```

## Troubleshooting

### Windows context menu does not appear

Re-register the menu:

```powershell
python .\Converter.py
```

Restart Explorer:

```powershell
taskkill /f /im explorer.exe
start explorer.exe
```

### Windows still uses an old folder command

Clean older entries:

```powershell
python .\cleanup_old_folder_menu.py
python .\Converter.py
```

Then restart Explorer.

### A terminal window appears on Windows

Confirm that source-mode Registry commands use `pythonw.exe`.

For packaged releases, confirm that both executables were built with `--windowed`.

### Batch GUI does not open on Windows

Confirm that `pythonw.exe` exists beside the installed Python executable when running from source.

For packaged builds, confirm this file exists beside the main executable:

```text
UwUConverterBatch.exe
```

### Batch GUI does not open on Linux

Install Tkinter for the distribution and try launching directly:

```bash
python3 BatchLauncher.py "/path/to/folder"
```

For packaged builds, confirm this file exists:

```text
UwUConverterBatch
```

### Old Dolphin batch menus remain

Run:

```bash
python3 cleanup_linux_menus.py
python3 Converter.py
```

Restart Dolphin afterward.

### Compression does not reach the exact requested size

Compression percentages are targets. Codecs, containers, and source characteristics affect the final result.

### Lossless compression barely changes the size

The original may already be efficiently compressed.

### Some batch files are skipped

A destination file may already exist, the file may not match the selected category, or the source may already use the selected output format.

Check the optional log for exact reasons.

### A document loses formatting

Document conversion focuses mainly on text rather than exact layout reconstruction.

### A spreadsheet loses formulas or formatting

Spreadsheet conversion focuses mainly on cell values.

### A RAW file fails

The file may not be recognized by rawpy and LibRaw, or it may be headerless raw pixel data rather than a supported camera RAW format.

## Reporting Bugs

Include:

- Operating system
- Linux distribution, when applicable
- Desktop environment
- File manager
- Source or packaged build
- Input extension
- Selected conversion action
- Full error message or traceback
- Source codecs for media issues
- Whether the issue affects single conversion, batch conversion, or both
- Whether logging was enabled
- Any formatting or workbook features that were lost

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for development setup, project structure, testing expectations, and pull request guidance.

## License

UwUConverter is licensed under the MIT License.

You may use, copy, modify, distribute, sublicense, and sell copies of the software, provided that the original copyright and license notice are preserved.

The software is provided without warranty. See the `LICENSE` file for the complete terms.

## Development Status

UwUConverter is a learning project under active development.

Windows is currently the most tested platform.

Linux integration and packaged Linux releases are experimental and still require broader testing across distributions, desktop environments, file managers, codecs, and unusual file formats.
