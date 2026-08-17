#!/usr/bin/env bash
set -euo pipefail

UPDATE_MODE=0

for argument in "$@"; do
    case "$argument" in
        --update)
            UPDATE_MODE=1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/UwUConverter"
BIN_DIR="$HOME/.local/bin"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/uwuconverter-updater.desktop"

mkdir -p "$APP_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$AUTOSTART_DIR"

# Copy the packaged application folder into a stable user location.
# cp -a intentionally overlays the previous install during an update.
cp -a "$SCRIPT_DIR/." "$APP_DIR/"

chmod +x "$APP_DIR/UwUConverterGUI" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterBatch" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterUpdater" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterBrowserHost" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterBrowserSetup" 2>/dev/null || true
chmod +x "$APP_DIR/cli/UwUConverter" 2>/dev/null || true

ln -sfn "$APP_DIR/cli/UwUConverter" "$BIN_DIR/UwUConverter"

if [ -x "$APP_DIR/UwUConverterUpdater" ]; then
    ESCAPED_UPDATER=${APP_DIR//\\/\\\\}
    ESCAPED_UPDATER=${ESCAPED_UPDATER//\"/\\\"}

    cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=UwUConverter Updater
Comment=Check for UwUConverter updates
Exec="$ESCAPED_UPDATER/UwUConverterUpdater" --auto
Terminal=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF
fi

# Refresh file-manager and native browser-host integrations using the newly installed build.
"$APP_DIR/UwUConverterGUI"

# Offer browser-extension installation. --auto suppresses repeat prompts on
# updates for browsers that have already been offered setup.
if [ -x "$APP_DIR/UwUConverterBrowserSetup" ]; then
    "$APP_DIR/UwUConverterBrowserSetup" --auto >/dev/null 2>&1 &
fi

# A fresh install gets an initial non-blocking update check. During an
# update this would only re-check the release that was just installed.
if [ "$UPDATE_MODE" -eq 0 ] && [ -x "$APP_DIR/UwUConverterUpdater" ]; then
    "$APP_DIR/UwUConverterUpdater" --auto >/dev/null 2>&1 &
fi

# The updater extracts release packages into /tmp. Clean that package
# after the detached installer has finished copying it.
if [ -n "${UWUCONVERTER_UPDATE_TEMP:-}" ]; then
    CLEANUP_TARGET="$UWUCONVERTER_UPDATE_TEMP"
    (
        sleep 2
        rm -rf -- "$CLEANUP_TARGET"
    ) >/dev/null 2>&1 &
fi

echo
if [ "$UPDATE_MODE" -eq 1 ]; then
    echo "Updated UwUConverter."
else
    echo "Installed UwUConverter."
fi

echo "CLI command: UwUConverter"
echo
echo "If ~/.local/bin is not currently in PATH, add this to your shell profile:"
echo 'export PATH="$HOME/.local/bin:$PATH"'
