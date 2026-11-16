#!/usr/bin/env bash
set -euo pipefail

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DIR="$DATA_HOME/UwUConverter"
CLI_LINK="$HOME/.local/bin/UwUConverter"
AUTOSTART_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/uwuconverter-updater.desktop"
STATE_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/UwUConverter"
ICON_FILE="$DATA_HOME/icons/hicolor/128x128/apps/uwuconverter.png"

if [ -x "$APP_DIR/UwUConverterGUI" ]; then
    "$APP_DIR/UwUConverterGUI" --uninstall || true
fi

if [ -L "$CLI_LINK" ] || [ -f "$CLI_LINK" ]; then
    rm -f "$CLI_LINK"
fi

rm -f "$AUTOSTART_FILE"
rm -f "$ICON_FILE"
rm -rf "$STATE_DIR"
rm -rf "$APP_DIR"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$DATA_HOME/icons/hicolor" >/dev/null 2>&1 || true
fi


echo "UwUConverter removed."
