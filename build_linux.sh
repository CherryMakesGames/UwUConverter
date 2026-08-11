#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

# Arch/CachyOS and other PEP 668 distributions block system-wide pip.
# Prefer the project's .venv when present; otherwise create an isolated
# build environment.
if [ -x ".venv/bin/python" ]; then
    BUILD_PYTHON=".venv/bin/python"
else
    BUILD_VENV=".uwu-build-venv"

    if [ ! -x "$BUILD_VENV/bin/python" ]; then
        python3 -m venv "$BUILD_VENV"
    fi

    BUILD_PYTHON="$BUILD_VENV/bin/python"
fi

"$BUILD_PYTHON" -m pip install --upgrade pip
"$BUILD_PYTHON" -m pip install -r requirements.txt

rm -rf build dist dist-cli dist-updater

# GUI used for file-manager registration and right-click conversions.
"$BUILD_PYTHON" -m PyInstaller \
  --clean \
  --noconfirm \
  --onedir \
  --windowed \
  --name UwUConverterGUI \
  --add-data "UwUConverter.ico:." \
  Converter.py

# Batch GUI.
"$BUILD_PYTHON" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --windowed \
  --name UwUConverterBatch \
  BatchLauncher.py

# CLI.
"$BUILD_PYTHON" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --name UwUConverter \
  --distpath dist-cli \
  cli.py

# Small windowless updater. It only uses the standard library + Tk.
"$BUILD_PYTHON" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --windowed \
  --name UwUConverterUpdater \
  --distpath dist-updater \
  updater.py

mkdir -p dist/UwUConverterGUI/cli

cp dist/UwUConverterBatch \
  dist/UwUConverterGUI/UwUConverterBatch

cp dist-cli/UwUConverter \
  dist/UwUConverterGUI/cli/UwUConverter

cp dist-updater/UwUConverterUpdater \
  dist/UwUConverterGUI/UwUConverterUpdater

cp install_linux.sh \
  dist/UwUConverterGUI/install.sh

cp uninstall_linux.sh \
  dist/UwUConverterGUI/uninstall.sh

chmod +x dist/UwUConverterGUI/UwUConverterGUI
chmod +x dist/UwUConverterGUI/UwUConverterBatch
chmod +x dist/UwUConverterGUI/UwUConverterUpdater
chmod +x dist/UwUConverterGUI/cli/UwUConverter
chmod +x dist/UwUConverterGUI/install.sh
chmod +x dist/UwUConverterGUI/uninstall.sh

case "$(uname -m)" in
  x86_64|amd64)
    RELEASE_ARCH="x86_64"
    ;;
  aarch64|arm64)
    RELEASE_ARCH="arm64"
    ;;
  *)
    RELEASE_ARCH="$(uname -m)"
    ;;
esac

RELEASE_ARCHIVE="dist/UwUConverter-linux-${RELEASE_ARCH}.tar.gz"
rm -f "$RELEASE_ARCHIVE"

tar \
  -C dist \
  -czf "$RELEASE_ARCHIVE" \
  UwUConverterGUI

echo
echo "Linux package directory:"
echo "  dist/UwUConverterGUI"
echo
echo "Linux release asset:"
echo "  $RELEASE_ARCHIVE"
echo
echo "Install with:"
echo "  ./dist/UwUConverterGUI/install.sh"
