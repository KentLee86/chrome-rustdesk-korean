"""Run inside a fresh test container; exercise actual browser and IME."""
import os
from pathlib import Path
import socket
import subprocess
import sys
from patchright.sync_api import sync_playwright

for process in Path('/proc').iterdir():
    if process.name.isdigit():
        try:
            if (process / 'comm').read_text().strip() == 'fcitx5':
                for value in (process / 'environ').read_bytes().split(b'\0'):
                    if value.startswith(b'DBUS_SESSION_BUS_ADDRESS='):
                        os.environ['DBUS_SESSION_BUS_ADDRESS'] = value.split(b'=', 1)[1].decode()
        except (FileNotFoundError, PermissionError):
            pass

with socket.create_connection(('127.0.0.1', 5900), timeout=5) as connection:
    version = connection.recv(12)
    assert version.startswith(b'RFB '), version
    connection.sendall(b'RFB 003.008\n')
    count = connection.recv(1)[0]
    methods = connection.recv(count)
    assert 2 in methods and 1 not in methods, 'VNC allows unauthenticated access'

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    context = browser.contexts[0]
    mode = sys.argv[1] if len(sys.argv) > 1 else 'desktop'
    if mode == 'set-cookie':
        context.add_cookies([{'name': 'smoke', 'value': 'persisted', 'domain': 'example.com', 'path': '/', 'expires': 2000000000}])
    elif mode == 'has-cookie':
        assert any(c['name'] == 'smoke' for c in context.cookies('https://example.com')), 'Profile was lost'
    elif mode == 'no-cookie':
        assert not any(c['name'] == 'smoke' for c in context.cookies('https://example.com')), 'Temporary profile retained the test cookie'
    else:
        page = context.new_page()
        try:
            page.set_content('<title>Input test</title><input id="test" autofocus>')
            page.bring_to_front()
            page.locator('#test').focus()
            subprocess.run(['fcitx5-remote', '-c'], check=True)
            if '--negative' not in sys.argv:
                subprocess.run(['xdotool', 'key', 'ctrl+space'], check=True)
            page.wait_for_timeout(300)
            subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '100', 'gksrmf'], check=True)
            subprocess.run(['xdotool', 'key', 'space'], check=True)
            page.wait_for_timeout(300)
            assert page.locator('#test').input_value() == '한글 ', page.locator('#test').input_value()
            subprocess.run(['xdotool', 'key', 'ctrl+space'], check=True)
            page.wait_for_timeout(200)
            subprocess.run(['xdotool', 'type', '--clearmodifiers', '--delay', '80', 'english'], check=True)
            assert page.locator('#test').input_value() == '한글 english'
        finally:
            page.close()
print('PASS:', mode, 'VNC requires authentication')
