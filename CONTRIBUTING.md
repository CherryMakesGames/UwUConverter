# Contributing to UwUConverter

Thanks for taking the time to contribute to UwUConverter!

UwUConverter is still growing, so contributions of any size are welcome. This includes bug fixes, new file formats, compression improvements, documentation updates, installer fixes, and general quality-of-life improvements.

## Before contributing

Please check the existing issues and pull requests before starting work. This helps avoid duplicate work and makes it easier to coordinate larger changes.

For bigger features, open an issue first and briefly explain:

- What problem the feature solves
- Which file formats or parts of the app it affects
- How you plan to implement it
- Any new dependencies it would require

## Setting up the project

Clone the repository and install the dependencies:

```powershell
git clone <repository-url>
cd UwUConverter
pip install -r requirements.txt
```

Run the project from source:

```powershell
python .\Converter.py
```

Running `Converter.py` without conversion arguments registers or refreshes the Windows right-click menu.

## Project structure

The project is split into separate modules:

- `Converter.py` - main entry point and conversion router
- `file_types.py` - supported extensions and right-click menu layout
- `make_key.py` - Windows Registry integration
- `video_converter.py` - video conversion
- `audio_converter.py` - audio conversion
- `image_converter.py` - image and RAW conversion
- `compression.py` - image and video compression
- `document_converter.py` - document conversion
- `spreadsheet_converter.py` - spreadsheet conversion

Try to keep new conversion logic inside the correct module instead of placing everything in `Converter.py`.

## Adding a new format

When adding a new format:

1. Add its context-menu entry in `file_types.py`.
2. Add the conversion logic to the correct converter module.
3. Route the new action through `Converter.py`.
4. Add any new package to `requirements.txt`.
5. Test both conversion from source and the packaged application.
6. Update the README with the new supported format.

Keep action names consistent between `file_types.py` and `Converter.py`.

## Compression contributions

Compression options currently include:

- Lossless optimization
- Compress by 25%
- Compress by 50%
- Compress by 75%

Percentage-based compression aims for a smaller target file size, but exact results may vary depending on the source format, codec, image content, and how optimized the original file already is.

Changes to compression should preserve the original file extension unless the conversion explicitly says otherwise.

## Code style

Please keep the existing code style:

- Use clear function and variable names
- Keep functions focused on one job
- Use straight apostrophes
- Avoid unnecessary dependencies
- Add useful error messages
- Keep formatting readable
- Do not silently overwrite the original file

Code does not need to be perfect, but it should be understandable and tested.

## Testing

Before opening a pull request, test:

- The conversion completes successfully
- The output file opens correctly
- Audio and video streams are preserved where expected
- The original file is not modified
- The right-click menu action points to the correct conversion
- The project still runs through Python
- The PyInstaller build still works
- The Inno Setup installer still installs and uninstalls correctly

Please mention which formats and files you tested in the pull request.

## Pull requests

Keep pull requests focused on one feature or fix when possible.

Include:

- A short explanation of the change
- Why the change is useful
- Files or formats affected
- Testing performed
- Screenshots for menu, installer, or GUI changes when relevant

## Bug reports

When reporting a bug, include:

- Input file format
- Selected conversion
- Expected result
- Actual result
- Error message or traceback
- Whether you used the source version or installed version
- Windows version
- A small sample file when it is safe to share

Do not upload private or sensitive files.

## Installer changes

Installer changes are handled through Inno Setup.

Please test that:

- The application appears in Windows Installed Apps
- The context menu is registered after installation
- All PyInstaller files are copied
- Uninstall removes the context-menu entries
- Existing user files are not deleted

## Documentation

Documentation improvements are always welcome. Try to keep instructions beginner-friendly and avoid assuming that every user is familiar with Python, PyInstaller, Inno Setup, or the Windows Registry.

## License

By contributing, you agree that your contributions may be distributed under the same license as UwUConverter.
