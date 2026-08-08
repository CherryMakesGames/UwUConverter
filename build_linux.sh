#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

rm -rf build dist dist-cli

# GUI used for file-manager registration and right-click conversions.
python3 -m PyInstaller \
  --clean \
  --noconfirm \
  --onedir \
  --windowed \
  --name UwUConverterGUI \
  --add-data "UwUConverter.ico:." \
  Converter.py

# Batch GUI.
python3 -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --windowed \
  --name UwUConverterBatch \
  BatchLauncher.py

# CLI. It is deliberately a console application and is named exactly
# UwUConverter so the installed command is:
#
#   UwUConverter convert ...
python3 -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --name UwUConverter \
  --distpath dist-cli \
  cli.py

mkdir -p dist/UwUConverterGUI/cli

cp dist/UwUConverterBatch \
  dist/UwUConverterGUI/UwUConverterBatch

cp dist-cli/UwUConverter \
  dist/UwUConverterGUI/cli/UwUConverter

cp install_linux.sh \
  dist/UwUConverterGUI/install.sh

cp uninstall_linux.sh \
  dist/UwUConverterGUI/uninstall.sh

chmod +x dist/UwUConverterGUI/UwUConverterGUI
chmod +x dist/UwUConverterGUI/UwUConverterBatch
chmod +x dist/UwUConverterGUI/cli/UwUConverter
chmod +x dist/UwUConverterGUI/install.sh
chmod +x dist/UwUConverterGUI/uninstall.sh

echo
echo "Linux package directory:"
echo "  dist/UwUConverterGUI"
echo
echo "Install with:"
echo "  ./dist/UwUConverterGUI/install.sh"
