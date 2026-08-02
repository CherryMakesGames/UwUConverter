# UwUConverter

UwUConverter is a small Windows file converter written in Python. It adds conversion options to the File Explorer right-click menu for supported file types.

The project currently supports video, audio, image, and camera RAW conversions.

## Features

- Adds a custom `Convert With UwUConverter ^-^` submenu to Windows File Explorer
- Different conversion options for each file extension
- Video remuxing when the original codecs are compatible with the target container
- Video and audio transcoding through PyAV and FFmpeg
- Image conversion through Pillow
- Camera RAW image conversion through rawpy
- Copies the application icon to a persistent local folder for use in the context menu
- Prints a full traceback and keeps the terminal open when a conversion fails

## Supported formats

### Video input

- MP4
- MKV
- MOV
- AVI
- WebM

Available output options depend on the source format and include:

- MP4
- MKV
- MOV
- AVI
- WebM
- MP3
- WAV
- FLAC
- OGG
- OPUS

### Audio input

- MP3
- WAV
- OGG
- FLAC
- OPUS

Available output options include:

- MP3
- WAV
- FLAC
- OGG
- OPUS

### Image input

- PNG
- JPG
- JPEG
- WebP
- ICO
- RAW

Available output options include:

- PNG
- JPG
- JPEG
- WebP
- ICO
- PDF

RAW is input-only. The program does not convert regular images into RAW files.

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- FFmpeg codecs available through the installed PyAV build

Install the Python dependencies:

```powershell
pip install av pillow rawpy
```

## Project files

Keep these files in the same folder:

```text
Converter.py
make_key.py
UwUConverter.ico
```

`Converter.py` handles file conversion.

`make_key.py` creates and resets the Windows File Explorer context-menu entries.

`UwUConverter.ico` is copied to the application's local data folder and used as the context-menu icon.

## Installation

Open PowerShell in the project folder and run:

```powershell
python .\Converter.py
```

When `Converter.py` is launched without conversion arguments, it installs or refreshes the right-click menu entries.

The icon is copied to:

```text
%LOCALAPPDATA%\UwUConverter\icon.ico
```

Registry entries are created under:

```text
HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations
```

Administrator privileges should not normally be required because the entries are created for the current user.

## Usage

1. Right-click a supported file in File Explorer.
2. Open `Convert With UwUConverter ^-^`.
3. Select the desired output format.
4. Wait for the terminal window to finish the conversion.

The converted file is saved beside the original file with the new extension.

Example:

```text
video.mkv -> video.mp4
song.wav -> song.opus
photo.raw -> photo.png
```

## Running a conversion manually

The converter can also be launched from PowerShell:

```powershell
python .\Converter.py "D:\Videos\example.mkv" "WEBM"
```

The first argument is the input file path.

The second argument is the requested output format.

## Remuxing and transcoding

Some video conversions use remuxing. Remuxing copies the original encoded audio and video streams into another container without re-encoding them.

This is fast and does not reduce quality, but it only works when the destination container supports the source codecs.

Other conversions require transcoding. Transcoding decodes and re-encodes the media using codecs appropriate for the destination format.

For example, WebM output uses:

```text
Video: VP8
Audio: Opus
```

Audio-only output uses codecs such as:

```text
MP3: libmp3lame
WAV: pcm_s16le
FLAC: flac
OGG: Vorbis
OPUS: libopus
```

## Camera RAW support

RAW files are opened with `rawpy` and converted into a normal RGB image before being saved through Pillow.

Camera RAW is not one universal format. Support depends on whether `rawpy` and LibRaw recognize the specific camera file.

Headerless raw pixel-data files are not supported because they require extra information such as:

- Image width
- Image height
- Bit depth
- Channel order
- Pixel format

## Known limitations

- Not every codec can be remuxed into every container.
- Unsupported video or audio codec combinations may require additional transcoding settings.
- Subtitle, attachment, and data streams may be skipped.
- Converting large videos with VP8 can be slow.
- The current interface does not display a graphical progress bar.
- Existing output files with the same name may be overwritten or cause an error depending on the format and backend.
- Document and spreadsheet formats listed as future categories are not currently implemented.

## Updating the context menu

After changing `file_types`, run:

```powershell
python .\Converter.py
```

The program removes its previous registry entries and creates them again using the current conversion list.

Windows Explorer may cache old menu icons. Restart Explorer when necessary:

```powershell
taskkill /f /im explorer.exe
start explorer.exe
```

## Troubleshooting

### The terminal closes immediately

The script prints a traceback and waits for Enter when it catches an error. Run it directly from PowerShell to see startup errors that occur before the exception handler.

### The context-menu icon is missing

Confirm that this file exists:

```powershell
Test-Path "$env:LOCALAPPDATA\UwUConverter\icon.ico"
```

It should return:

```text
True
```

Then restart Windows Explorer.

### A video conversion fails

The source codec may not be compatible with the selected container. A remux cannot change the codec, so the conversion may need a dedicated transcoding configuration.

### A RAW image does not open

The file may not be a camera RAW format supported by LibRaw. A `.raw` extension by itself does not describe the image layout.

## Development status

UwUConverter is a learning project and is still under development. Some formats and codec combinations may not work yet, and the conversion settings may change as support improves.

## License

UwUConverter is licensed under the MIT License. See the `LICENSE` file for details.
