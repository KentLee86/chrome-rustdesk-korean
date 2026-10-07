#!/bin/bash
set -uo pipefail
# Forward Docker's stop signal to the desktop, keeping D-Bus alive while Chrome flushes.
rm -f /run/remote-chrome/desktop.pid
dbus-run-session -- /usr/local/bin/start-desktop &
session_pid=$!
stop() {
    if [ -f /run/remote-chrome/desktop.pid ]; then
        kill -TERM "$(cat /run/remote-chrome/desktop.pid)" 2>/dev/null || true
    else
        kill -TERM "$session_pid" 2>/dev/null || true
    fi
}
trap stop TERM INT
status=0
wait "$session_pid" || status=$?
# A trapped signal interrupts wait before the child has finished its cleanup.
if kill -0 "$session_pid" 2>/dev/null; then
    if wait "$session_pid"; then status=0; else status=$?; fi
fi
exit "$status"
