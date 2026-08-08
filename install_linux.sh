#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/UwUConverter"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$APP_DIR"
mkdir -p "$BIN_DIR"

# Copy the packaged application folder into a stable user location.
cp -a "$SCRIPT_DIR/." "$APP_DIR/"

chmod +x "$APP_DIR/UwUConverterGUI" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterBatch" 2>/dev/null || true
chmod +x "$APP_DIR/cli/UwUConverter" 2>/dev/null || true

ln -sfn "$APP_DIR/cli/UwUConverter" "$BIN_DIR/UwUConverter"

"$APP_DIR/UwUConverterGUI"

echo
echo "Installed UwUConverter."
echo "CLI command: UwUConverter"
echo
echo "If ~/.local/bin is not currently in PATH, add this to your shell profile:"
echo 'export PATH="$HOME/.local/bin:$PATH"'
