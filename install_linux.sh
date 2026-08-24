#!/usr/bin/env bash
set -euo pipefail

UPDATE_MODE=0
FROM_GUI=0
SKIP_BROWSER_QUESTIONS=0
INSTALL_CLI=1
INSTALL_UPDATER=1

for argument in "$@"; do
    case "$argument" in
        --update)
            UPDATE_MODE=1
            ;;
        --from-gui)
            FROM_GUI=1
            ;;
        --skip-browser-questions)
            SKIP_BROWSER_QUESTIONS=1
            ;;
        --no-cli)
            INSTALL_CLI=0
            ;;
        --no-updater)
            INSTALL_UPDATER=0
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Compatibility bridge for users updating from an older UwUConverter updater.
# Older updater builds launch "install.sh --update" directly. New release
# packages redirect that call into the graphical installer when a desktop
# session is available, so even the first update to this installer-enabled
# version can show the GUI.
if [ "$UPDATE_MODE" -eq 1 ] &&    [ "$FROM_GUI" -eq 0 ] &&    [ -x "$SCRIPT_DIR/UwUConverterInstaller" ] &&    [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]; then
    INSTALLER_ARGS=(--update)

    if [ -n "${UWUCONVERTER_UPDATE_TEMP:-}" ]; then
        INSTALLER_ARGS+=(
            --update-temp
            "$UWUCONVERTER_UPDATE_TEMP"
        )
    fi

    exec "$SCRIPT_DIR/UwUConverterInstaller" "${INSTALLER_ARGS[@]}"
fi
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/UwUConverter"
BIN_DIR="$HOME/.local/bin"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/uwuconverter-updater.desktop"

mkdir -p "$APP_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$AUTOSTART_DIR"

# Copy the packaged application folder into a stable user location.
# cp -a intentionally overlays the previous install during an update.
# Skip the copy when install.sh is already running from the installed folder.
if [ "$SCRIPT_DIR" != "$APP_DIR" ]; then
    cp -a "$SCRIPT_DIR/." "$APP_DIR/"
fi

chmod +x "$APP_DIR/UwUConverterGUI" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterBatch" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterUpdater" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterBrowserHost" 2>/dev/null || true
chmod +x "$APP_DIR/UwUConverterInstaller" 2>/dev/null || true
chmod +x "$APP_DIR/cli/UwUConverter" 2>/dev/null || true

if [ "$INSTALL_CLI" -eq 1 ]; then
    ln -sfn "$APP_DIR/cli/UwUConverter" "$BIN_DIR/UwUConverter"
else
    rm -f "$BIN_DIR/UwUConverter"
fi

if [ "$INSTALL_UPDATER" -eq 1 ] && [ -x "$APP_DIR/UwUConverterUpdater" ]; then
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
else
    rm -f "$AUTOSTART_FILE"
fi

first_command() {
    local candidate
    for candidate in "$@"; do
        if command -v "$candidate" >/dev/null 2>&1; then
            command -v "$candidate"
            return 0
        fi
    done
    return 1
}

flatpak_installed() {
    command -v flatpak >/dev/null 2>&1 || return 1
    flatpak info "$1" >/dev/null 2>&1
}

ask_browser_question() {
    local browser_name="$1"
    local message="Install the UwUConverter browser extension for ${browser_name}?"

    if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && command -v kdialog >/dev/null 2>&1; then
        kdialog --yesno "$message" --title "UwUConverter Browser Integration"
        return $?
    fi

    if [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] && command -v zenity >/dev/null 2>&1; then
        zenity --question --title="UwUConverter Browser Integration" --text="$message"
        return $?
    fi

    if [ -t 0 ]; then
        printf '%s [Y/n] ' "$message"
        read -r answer
        case "${answer:-y}" in
            y|Y|yes|YES|Yes) return 0 ;;
            *) return 1 ;;
        esac
    fi

    return 1
}

open_extension_folder_once() {
    local family="$1"
    local folder="$APP_DIR/browser-extension/$family"
    [ -d "$folder" ] || return 0

    if [ "$family" = "chromium" ] && [ "${CHROMIUM_FOLDER_OPENED:-0}" -eq 1 ]; then return 0; fi
    if [ "$family" = "firefox" ] && [ "${FIREFOX_FOLDER_OPENED:-0}" -eq 1 ]; then return 0; fi

    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$folder" >/dev/null 2>&1 &
    fi

    if [ "$family" = "chromium" ]; then CHROMIUM_FOLDER_OPENED=1; else FIREFOX_FOLDER_OPENED=1; fi
}

offer_native_browser() {
    local browser_name="$1"
    local manager_url="$2"
    local family="$3"
    shift 3
    local executable
    executable="$(first_command "$@")" || return 0

    if ask_browser_question "$browser_name"; then
        "$executable" "$manager_url" >/dev/null 2>&1 &
        open_extension_folder_once "$family"
    fi
}

offer_flatpak_browser() {
    local browser_name="$1"
    local app_id="$2"
    local manager_url="$3"
    local family="$4"
    flatpak_installed "$app_id" || return 0

    if ask_browser_question "$browser_name (Flatpak)"; then
        flatpak run "$app_id" "$manager_url" >/dev/null 2>&1 &
        open_extension_folder_once "$family"
    fi
}

offer_browser_integrations() {
    CHROMIUM_FOLDER_OPENED=0
    FIREFOX_FOLDER_OPENED=0

    offer_native_browser "Google Chrome" "chrome://extensions" "chromium" google-chrome google-chrome-stable
    offer_native_browser "Chromium" "chrome://extensions" "chromium" chromium chromium-browser
    offer_native_browser "Microsoft Edge" "edge://extensions" "chromium" microsoft-edge microsoft-edge-stable microsoft-edge-beta microsoft-edge-dev
    offer_native_browser "Opera" "opera://extensions" "chromium" opera opera-stable opera-beta opera-developer
    offer_native_browser "Opera GX" "opera://extensions" "chromium" opera-gx opera-gx-stable
    offer_native_browser "Brave" "brave://extensions" "chromium" brave-browser brave-browser-stable brave
    offer_native_browser "Vivaldi" "vivaldi://extensions" "chromium" vivaldi vivaldi-stable vivaldi-snapshot
    offer_native_browser "Firefox" "about:debugging#/runtime/this-firefox" "firefox" firefox firefox-esr

    offer_flatpak_browser "Google Chrome" "com.google.Chrome" "chrome://extensions" "chromium"
    offer_flatpak_browser "Chromium" "org.chromium.Chromium" "chrome://extensions" "chromium"
    offer_flatpak_browser "Microsoft Edge" "com.microsoft.Edge" "edge://extensions" "chromium"
    offer_flatpak_browser "Opera" "com.opera.Opera" "opera://extensions" "chromium"
    offer_flatpak_browser "Opera GX" "com.opera.opera-gx" "opera://extensions" "chromium"
    offer_flatpak_browser "Brave" "com.brave.Browser" "brave://extensions" "chromium"
    offer_flatpak_browser "Vivaldi" "com.vivaldi.Vivaldi" "vivaldi://extensions" "chromium"
    offer_flatpak_browser "Firefox" "org.mozilla.firefox" "about:debugging#/runtime/this-firefox" "firefox"
}

# Refresh file-manager and native browser-host integrations using the newly installed build.
"$APP_DIR/UwUConverterGUI"

# Browser questions are part of the initial Linux installer itself.
# Updates skip them so users are not asked again on every update.
if [ "$UPDATE_MODE" -eq 0 ] && [ "$SKIP_BROWSER_QUESTIONS" -eq 0 ]; then
    offer_browser_integrations
fi

# A fresh install gets an initial non-blocking update check. During an
# update this would only re-check the release that was just installed.
if [ "$UPDATE_MODE" -eq 0 ] &&    [ "$INSTALL_UPDATER" -eq 1 ] &&    [ -x "$APP_DIR/UwUConverterUpdater" ]; then
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
