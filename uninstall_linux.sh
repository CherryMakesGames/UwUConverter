#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/UwUConverter"
CLI_LINK="$HOME/.local/bin/UwUConverter"

if [ -x "$APP_DIR/UwUConverterGUI" ]; then
    "$APP_DIR/UwUConverterGUI" --uninstall || true
fi

if [ -L "$CLI_LINK" ] || [ -f "$CLI_LINK" ]; then
    rm -f "$CLI_LINK"
fi

rm -rf "$APP_DIR"

echo "UwUConverter removed."
