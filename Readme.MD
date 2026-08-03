# UwUConverter

UwUConverter is a Windows file converter written in Python. It adds file conversion options directly to the File Explorer right-click menu, so supported files can be converted without opening a separate application.

The project currently supports video, audio, images, camera RAW files, documents, and spreadsheets.

## Download

Prebuilt Windows releases are available on the project's GitHub Releases page.

Download the latest:

```text
UwUConverter-Setup.exe
```

The installer places UwUConverter in a permanent application folder, registers the File Explorer context-menu entries, installs the icon, and adds an uninstaller.

A release build is the recommended option for most users because Python and the project's packages do not need to be installed manually.

## Features

- Adds a `Convert With UwUConverter ^-^` submenu to Windows File Explorer
- Shows different conversion options for each supported extension
- Supports media remuxing when the existing codecs are compatible
- Supports video and audio transcoding through PyAV and FFmpeg
- Converts images through Pillow
- Converts supported camera RAW images through rawpy
- Converts PDF files to DOCX through pdf2docx
- Converts DOCX, ODT, and TXT files without requiring LibreOffice
- Converts common spreadsheet formats without requiring Microsoft Excel or LibreOffice
- Installs and removes its own context-menu entries
- Prints complete error tracebacks when a conversion fails

## Supported formats

### Video input

- MP4
- MKV
- MOV
- AVI
- WebM

Available output options include MP4, MKV, MOV, AVI, WebM, MP3, WAV, FLAC, OGG, and OPUS.

### Audio input

- MP3
- WAV
- OGG
- FLAC
- OPUS

Available output options include MP3, WAV, FLAC, OGG, and OPUS.

### Image input

- PNG
- JPG
- JPEG
- WebP
- ICO
- RAW

Available output options include PNG, JPG, JPEG, WebP, ICO, and PDF.

RAW is input-only. UwUConverter does not convert ordinary images into RAW files.

### Document input

- PDF
- DOCX
- ODT
- TXT

Available output options include PDF, DOCX, ODT, and TXT.

PDF to DOCX conversion is handled through `pdf2docx`.

DOCX, ODT, TXT, and PDF conversions are mostly text-based. Complex formatting, images, tables, headers, footers, and exact page layouts may not be preserved.

Legacy binary `.doc` files are not currently supported.

### Spreadsheet input

- XLSX
- XLS
- XLSB
- XLSM
- ODS
- CSV
- TSV

Available output options include XLSX, XLS, ODS, CSV, TSV, and PDF.

Google Sheets is not a local file format. Export the sheet as XLSX, ODS, CSV, or TSV before converting it.

## Installing a GitHub release

1. Open the project's GitHub Releases page.
2. Download the newest `UwUConverter-Setup.exe`.
3. Run the installer.
4. Complete the installation.
5. Right-click a supported file in File Explorer.
6. Open `Convert With UwUConverter ^-^`.
7. Select the desired output format.

UwUConverter is normally installed under:

```text
%LOCALAPPDATA%\Programs\UwUConverter
```

Its context-menu icon is stored under:

```text
%LOCALAPPDATA%\UwUConverter\icon.ico
```

Administrator access should not normally be required because context-menu entries are registered under `HKEY_CURRENT_USER`.

## Usage

Right-click a supported file, open the UwUConverter submenu, and choose an output format.

The converted file is saved next to the original file.

Examples:

```text
video.mkv -> video.mp4
song.wav -> song.opus
photo.raw -> photo.png
document.docx -> document.pdf
spreadsheet.xlsx -> spreadsheet.csv
table.tsv -> table.ods
```

## Self-building

### Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- Inno Setup 6 for building the installer

Clone or download the repository, then open PowerShell in the project folder.

Install the Python packages:

```powershell
pip install -r requirements_no_libreoffice.txt
```

### Run from source

Keep these files in the same project folder:

```text
Converter.py
make_key.py
UwUConverter.ico
requirements_no_libreoffice.txt
```

Install or refresh the context menu:

```powershell
python .\Converter.py
```

Run a conversion manually:

```powershell
python .\Converter.py "D:\Videos\example.mkv" "WEBM"
```

Remove the registered context-menu entries:

```powershell
python .\Converter.py --uninstall
```

### Build the executable

Install PyInstaller:

```powershell
pip install pyinstaller
```

Build a single-file executable:

```powershell
pyinstaller --clean --noconfirm --onefile ^
  --name UwUConverter ^
  --icon UwUConverter.ico ^
  --add-data "UwUConverter.ico:." ^
  Converter.py
```

The executable will be created at:

```text
dist\UwUConverter.exe
```

Test the executable before building the installer:

```powershell
.\dist\UwUConverter.exe
```

### Build the Windows installer

Install Inno Setup 6 and open `installer.iss` in Inno Setup Compiler.

Compile it with:

```text
Build > Compile
```

or:

```text
Ctrl + F9
```

The installer will normally be created at:

```text
installer-output\UwUConverter-Setup.exe
```

## GitHub Actions builds

The repository can use GitHub Actions to build release files automatically.

A tagged release can:

1. Install the Python dependencies.
2. Build `UwUConverter.exe` with PyInstaller.
3. Compile `UwUConverter-Setup.exe` with Inno Setup.
4. Upload the installer as a workflow artifact.
5. Attach the installer to a GitHub Release.

Example version tag:

```powershell
git tag v1.0.0
git push origin v1.0.0
```

After the workflow finishes, the installer should appear on the GitHub Releases page.

## Remuxing and transcoding

Some video conversions use remuxing. Remuxing copies existing encoded streams into another container without re-encoding them.

This is fast and does not reduce quality, but it only works when the destination container supports the source codecs.

Other conversions require transcoding. Transcoding decodes and re-encodes the source using codecs supported by the selected output format.

WebM output currently uses:

```text
Video: VP8
Audio: Opus
```

Audio-only formats use codecs such as:

```text
MP3: libmp3lame
WAV: pcm_s16le
FLAC: flac
OGG: Vorbis
OPUS: libopus
```

## Camera RAW support

Camera RAW files are processed through rawpy and converted into an RGB image before being saved through Pillow.

RAW is not one universal format. Support depends on whether rawpy and LibRaw recognize the camera file.

Completely headerless raw pixel data is not supported because it requires additional information such as width, height, bit depth, channel order, and pixel format.

## Spreadsheet limitations

Spreadsheet conversions focus on cell data.

The following may be lost or changed:

- Formulas
- Macros
- Charts
- Pivot tables
- Cell styling
- Conditional formatting
- Multiple sheets when exporting to CSV or TSV
- Workbook-specific metadata

XLSM files can be read, but VBA macros are not preserved during conversion.

CSV and TSV only store one table and do not preserve workbook formatting or multiple sheets.

## Document limitations

Document conversions focus mainly on text content.

The following may be lost or changed:

- Fonts and text styling
- Images
- Tables
- Headers and footers
- Page breaks
- Footnotes
- Columns
- Exact spacing and pagination

PDF to DOCX results depend heavily on the structure of the original PDF.

## Updating the context menu

After changing `file_types`, run:

```powershell
python .\Converter.py
```

UwUConverter removes its old entries and recreates them from the current conversion list.

Windows Explorer may cache old icons or menu entries. Restart Explorer when necessary:

```powershell
taskkill /f /im explorer.exe
start explorer.exe
```

## Uninstalling

When installed through `UwUConverter-Setup.exe`, use the normal Windows uninstaller.

For a source installation, run:

```powershell
python .\Converter.py --uninstall
```

## Troubleshooting

### The context menu does not appear

Run UwUConverter once without conversion arguments:

```powershell
python .\Converter.py
```

For a release build:

```powershell
UwUConverter.exe
```

Then restart Windows Explorer.

### The context-menu icon is missing

Check whether the copied icon exists:

```powershell
Test-Path "$env:LOCALAPPDATA\UwUConverter\icon.ico"
```

It should return:

```text
True
```

### A video conversion fails

The source codecs may not be compatible with the selected container. Remuxing cannot change codecs, so that conversion may need a dedicated transcoding path.

### A document loses formatting

The current no-LibreOffice document conversion system focuses on extracting and recreating text rather than preserving full layout.

### A spreadsheet loses formatting or formulas

The spreadsheet conversion system focuses on cell values. Advanced Excel and workbook features are not guaranteed to survive.

## Reporting bugs

Include:

- Input extension
- Selected output format
- Full terminal traceback
- Source codecs for media problems
- Whether the problem happens in a release build or source build
- A description of any formatting or workbook features that were lost

## License

UwUConverter is licensed under the MIT License.

You may use, copy, modify, distribute, sublicense, and sell copies of the software, provided that the original copyright and license notice are preserved.

The software is provided without warranty. See the `LICENSE` file for the complete terms.

## Development status

UwUConverter is a learning project under active development. Some unusual codecs, camera RAW formats, documents, spreadsheets, and conversion combinations may not work correctly yet.
