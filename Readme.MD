# UwUConverter

![nya~](./Readme%20Images/banner.png)

UwUConverter is a local file converter written in Python. It adds conversion and compression options directly to the file manager's right-click menu, so supported files can be processed without opening a separate application.

Windows is currently the most complete version. Experimental Linux support is available for Nautilus, Nemo, Caja, and Dolphin.

## Usage Preview

![cOwOnvert Pwetty Pwease](./Readme%20Images/Screenshot%202026-08-04%20155327.png)
![cOwOmpress Pwease](./Readme%20Images/Screenshot%202026-08-04%20155443.png)

## Download

### Windows

Download the latest installer from the GitHub Releases page:

```text
UwUConverter-Setup.exe
```

The Inno Setup installer places UwUConverter in a permanent folder, registers the File Explorer menus, installs the icon, and adds uninstall support.

### Linux

Linux releases are currently experimental and distributed as a `.tar.gz` archive containing the PyInstaller folder.

```bash
tar -xzf UwUConverter-Linux-x64.tar.gz
chmod +x UwUConverter/UwUConverter
./UwUConverter/UwUConverter
```

Running UwUConverter without conversion arguments installs or refreshes the supported file-manager integrations.

## Features

- Adds conversion options directly to the right-click menu
- Groups music, video, image, document, spreadsheet, and compression actions
- Supports media remuxing where compatible
- Supports video and audio transcoding through PyAV and FFmpeg
- Converts images through Pillow
- Converts supported camera RAW images through rawpy
- Converts PDF files to DOCX through pdf2docx
- Converts DOCX, ODT, and TXT without LibreOffice
- Converts common spreadsheet formats without Microsoft Excel or LibreOffice
- Provides lossless, 25%, 50%, and 75% compression options
- Preserves the original video container during compression
- Installs and removes its own Windows and Linux menu integrations
- Uses separate converter modules for easier maintenance
- Prints full tracebacks when a conversion fails

## Compression

UwUConverter currently provides:

- Lossless optimization
- Compress by 25%
- Compress by 50%
- Compress by 75%

The percentage describes the intended reduction from the original size:

```text
25% compression -> aims for about 75% of the original size
50% compression -> aims for about 50% of the original size
75% compression -> aims for about 25% of the original size
```

Exact results vary. Codecs, metadata, container overhead, image contents, and existing compression can all affect the final size. Lossless optimization may produce almost no reduction when the source is already efficiently encoded.

## Supported formats

### Video input

- MP4
- MKV
- MOV
- AVI
- WebM

Outputs include MP4, MKV, MOV, AVI, WebM, MP3, WAV, FLAC, OGG, and OPUS.

### Audio input

- MP3
- WAV
- OGG
- FLAC
- OPUS

Outputs include MP3, WAV, FLAC, OGG, and OPUS.

### Image input

- PNG
- JPG
- JPEG
- WebP
- ICO
- RAW

Outputs include PNG, JPG, JPEG, WebP, ICO, and PDF.

RAW is input-only.

### Document input

- PDF
- DOCX
- ODT
- TXT

Outputs include PDF, DOCX, ODT, and TXT.

PDF-to-DOCX conversion uses `pdf2docx`. Other document conversions are mostly text-based, so complex layouts, tables, images, headers, and exact formatting may not survive.

Legacy `.doc` files are not currently supported.

### Spreadsheet input

- XLSX
- XLS
- XLSB
- XLSM
- ODS
- CSV
- TSV

Outputs include XLSX, XLS, ODS, CSV, TSV, and PDF.

Spreadsheet conversions focus on cell values. Macros, formulas, charts, formatting, pivot tables, and workbook metadata may be lost.

## Windows installation

1. Download `UwUConverter-Setup.exe`.
2. Run the installer.
3. Complete the installation.
4. Right-click a supported file.
5. Open `Convert With UwUConverter ^-^`.
6. Choose a conversion or compression action.

UwUConverter is normally installed under:

```text
%LOCALAPPDATA%\Programs\UwUConverter
```

The context-menu icon is stored under:

```text
%LOCALAPPDATA%\UwUConverter\icon.ico
```

Administrator access should not normally be required.

## Linux compatibility

Linux support currently includes:

- GNOME through Nautilus
- Cinnamon through Nemo
- MATE through Caja
- KDE Plasma through Dolphin

Compatibility depends on the file manager more than the desktop environment.

### Nautilus, Nemo, and Caja

UwUConverter generates scripts in:

```text
~/.local/share/nautilus/scripts/UwUConverter
~/.local/share/nemo/scripts/UwUConverter
~/.config/caja/scripts/UwUConverter
```

The actions appear in the file manager's `Scripts` submenu.

### KDE Plasma and Dolphin

UwUConverter generates Dolphin service menus in:

```text
~/.local/share/kio/servicemenus/
```

The actions appear in grouped UwUConverter right-click submenus.

Restart Dolphin when needed:

```bash
kquitapp6 dolphin
dolphin &
```

### Linux uninstall

```bash
./UwUConverter/UwUConverter --uninstall
```

When running from source:

```bash
python3 Converter.py --uninstall
```

## Usage

The result is saved beside the original file.

```text
video.mkv -> video.mp4
video.mkv -> video_compressed_50.mkv
song.wav -> song.opus
photo.raw -> photo.png
photo.png -> photo_compressed_25.png
document.docx -> document.pdf
spreadsheet.xlsx -> spreadsheet.csv
```

## Running from source

### Windows

```powershell
pip install -r requirements.txt
python .\Converter.py
```

Manual conversion:

```powershell
python .\Converter.py "D:\Videos\example.mkv" "WEBM"
```

Remove the menu entries:

```powershell
python .\Converter.py --uninstall
```

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python3 Converter.py
```

Manual conversion:

```bash
python3 Converter.py "/home/user/Videos/example.mkv" "WEBM"
```

## Building for Windows

```powershell
pyinstaller --clean --noconfirm --onedir ^
  --name UwUConverter ^
  --icon UwUConverter.ico ^
  --add-data "UwUConverter.ico;." ^
  Converter.py
```

The executable is created at:

```text
dist\UwUConverter\UwUConverter.exe
```

Compile `installer.iss` with Inno Setup 6. The installer is normally created at:

```text
installer-output\UwUConverter-Setup.exe
```

## Building for Linux

Linux builds must be created on Linux.

```bash
pyinstaller \
  --clean \
  --noconfirm \
  --onedir \
  --name UwUConverter \
  --add-data "UwUConverter.ico:." \
  Converter.py
```

The executable is created at:

```text
dist/UwUConverter/UwUConverter
```

Create the release archive:

```bash
cd dist
tar -czf UwUConverter-Linux-x64.tar.gz UwUConverter
```

Linux support should remain marked experimental until it has been tested across multiple distributions and desktops.

## Troubleshooting

### A compressed file is not exactly the requested size

Percentage compression uses a target. It cannot guarantee an exact final byte count because codecs and containers add overhead.

### A lossless file is not much smaller

The original may already be efficiently compressed.

### Dolphin actions do not appear

```bash
ls ~/.local/share/kio/servicemenus/uwuconverter-*.desktop
kquitapp6 dolphin
dolphin &
```

### Windows menus do not appear

Run UwUConverter once without conversion arguments and restart Explorer.

### A document loses formatting

The current document system focuses mainly on text content.

### A spreadsheet loses formatting or formulas

The current spreadsheet system focuses mainly on cell values.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Reporting bugs

Include:

- Operating system
- Desktop environment
- File manager
- Input extension
- Selected action
- Full traceback
- Source codecs for media issues
- Whether you used a source or release build

## License

UwUConverter is licensed under the MIT License.

## Development status

UwUConverter is a learning project under active development. Windows is the most tested platform. Linux support is experimental.
