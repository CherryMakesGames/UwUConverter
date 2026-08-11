#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/UwUConverter"
CLI_LINK="$HOME/.local/bin/UwUConverter"
AUTOSTART_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/uwuconverter-updater.desktop"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/UwUConverter"

if [ -x "$APP_DIR/UwUConverterGUI" ]; then
    "$APP_DIR/UwUConverterGUI" --uninstall || true
fi

if [ -L "$CLI_LINK" ] || [ -f "$CLI_LINK" ]; then
    rm -f "$CLI_LINK"
fi

rm -f "$AUTOSTART_FILE"
rm -rf "$STATE_DIR"
rm -rf "$APP_DIR"

echo "UwUConverter removed."
