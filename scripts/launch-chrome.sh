#!/bin/bash
# Based on Qrtr's host-side launcher, with a separate Campervan profile and port.
set -euo pipefail

PORT=9223
USER_DATA_DIR="${HOME}/.config/chrome-devtools-campervan"

detect_chrome() {
    if [[ -n "${CHROME_BIN:-}" ]]; then
        command -v "$CHROME_BIN"
        return
    fi

    for chrome_path in \
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
        "/usr/bin/google-chrome" \
        "/usr/bin/google-chrome-stable" \
        "/usr/bin/chromium" \
        "/usr/bin/chromium-browser" \
        "/snap/bin/chromium"; do
        if [[ -x "$chrome_path" ]]; then
            printf '%s\n' "$chrome_path"
            return 0
        fi
    done

    command -v chrome.exe
}

if ! CHROME_PATH=$(detect_chrome); then
    echo "Error: Could not find Chrome/Chromium. Install it or set CHROME_BIN to its executable." >&2
    exit 1
fi

mkdir -p "$USER_DATA_DIR"
echo "Starting Campervan Chrome with remote debugging at http://127.0.0.1:$PORT"
echo "Profile: $USER_DATA_DIR"

exec "$CHROME_PATH" \
    --remote-debugging-address=127.0.0.1 \
    --remote-debugging-port="$PORT" \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run \
    --no-default-browser-check
