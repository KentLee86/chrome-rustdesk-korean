#!/bin/bash
set -euo pipefail
export DISPLAY=:99 GTK_IM_MODULE=fcitx QT_IM_MODULE=fcitx XMODIFIERS=@im=fcitx
export XDG_RUNTIME_DIR=/run/remote-chrome
chmod 700 "$XDG_RUNTIME_DIR"
echo "$$" > "$XDG_RUNTIME_DIR/desktop.pid"
init-runtime
source "$XDG_RUNTIME_DIR/flags"
mkdir -p /data/chrome-profile "$HOME/.config/fcitx5"
for file in config profile; do
    if [ ! -f "$HOME/.config/fcitx5/$file" ]; then
        cp "/etc/remote-chrome/fcitx5/$file" "$HOME/.config/fcitx5/$file"
    fi
done
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
# Refuse an active profile; Chrome itself manages stale Singleton locks.
Xvfb :99 -screen 0 "${SCREEN_SIZE:-1400x1000x24}" -nolisten tcp &
pids=($!)
cleanup() {
    trap - EXIT TERM INT
    if [ "$ENABLE_CDP" = true ]; then
        timeout 5 python3 - <<'PY' || true
from patchright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    browser.new_browser_cdp_session().send('Browser.close')
PY
    fi
    # Give Chrome time to flush cookies and remove its profile lock before kill.
    if [ -n "${chrome_pid:-}" ]; then
        if [ "$ENABLE_CDP" != true ]; then
            # Ask the window manager to close Chrome normally, even without CDP.
            while read -r window; do
                xdotool windowactivate --sync "$window" key --clearmodifiers alt+F4 2>/dev/null || true
            done < <(xdotool search --onlyvisible --class google-chrome 2>/dev/null || true)
        fi
        for attempt in $(seq 1 50); do
            kill -0 "$chrome_pid" 2>/dev/null || break
            sleep 0.1
        done
    fi
    kill "${pids[@]}" 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 0' TERM INT
for attempt in $(seq 1 50); do
    xdpyinfo -display :99 >/dev/null 2>&1 && break
    sleep 0.1
done
xdpyinfo -display :99 >/dev/null
fluxbox >/tmp/fluxbox.log 2>&1 &
pids+=($!)
fcitx5 --replace >/tmp/fcitx5.log 2>&1 &
pids+=($!)
for attempt in $(seq 1 50); do
    state=$(fcitx5-remote 2>/dev/null || true)
    [ "${state:-0}" != 0 ] && break
    sleep 0.1
done
[ "${state:-0}" != 0 ] || { echo 'Input method failed to start' >&2; exit 1; }
x11vnc -display :99 -forever -shared -rfbauth "$XDG_RUNTIME_DIR/vnc.auth" \
    -rfbport 5900 -localhost -quiet >/tmp/x11vnc.log 2>&1 &
pids+=($!)
websockify --web /usr/share/novnc 6080 localhost:5900 >/tmp/novnc.log 2>&1 &
pids+=($!)
chrome_args=(--user-data-dir=/data/chrome-profile --no-first-run --no-default-browser-check
    --password-store=basic --window-position=0,0 --window-size=1400,1000)
if [ "$ENABLE_CDP" = true ]; then
    chrome_args+=(--remote-debugging-port=9222)
    socat TCP-LISTEN:9223,fork,reuseaddr TCP:127.0.0.1:9222 >/tmp/cdp-proxy.log 2>&1 &
    pids+=($!)
fi
google-chrome "${chrome_args[@]}" "${START_URL:-about:blank}" >/tmp/chrome.log 2>&1 &
chrome_pid=$!
pids+=("$chrome_pid")
if [ "$ENABLE_RUSTDESK" = true ]; then
    rustdesk --server >/tmp/rustdesk.log 2>&1 &
    pids+=($!)
fi
wait -n "${pids[@]}"
exit 1
