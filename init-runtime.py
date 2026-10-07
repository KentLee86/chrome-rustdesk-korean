#!/usr/bin/env python3
"""Initialize per-install secrets; never embed credentials in the image."""
import json
import os
from pathlib import Path
import secrets
import subprocess


def enabled(name, default):
    value = os.environ.get(name, default).lower()
    if value not in ("true", "false"):
        raise ValueError(f"{name} must be true or false")
    return value == "true"


def password(name, saved):
    source = os.environ.get(name + "_FILE")
    supplied = Path(source).read_text().rstrip("\r\n") if source else os.environ.get(name)
    value = supplied if supplied is not None else (
        saved.read_text().strip() if saved.exists() else secrets.token_urlsafe(24)
    )
    if not value or "\n" in value or "\r" in value:
        raise ValueError(f"{name} must be a nonempty single line")
    if name == "VNC_PASSWORD" and (not value.isascii() or len(value) < 8):
        raise ValueError("VNC_PASSWORD must contain at least 8 ASCII characters")
    if name == "RUSTDESK_PASSWORD" and len(value) < 12:
        raise ValueError("RUSTDESK_PASSWORD must contain at least 12 characters")
    saved.write_text(value + "\n")
    saved.chmod(0o600)
    return value


def main():
    os.umask(0o077)
    rustdesk = enabled("ENABLE_RUSTDESK", "true")
    cdp = enabled("ENABLE_CDP", "false")
    runtime = Path(os.environ.get("RUNTIME_DIR", "/run/remote-chrome"))
    config = Path(os.environ.get("CONFIG_DIR", "/config"))
    runtime.mkdir(parents=True, exist_ok=True)
    config.mkdir(parents=True, exist_ok=True)
    vnc = password("VNC_PASSWORD", config / "vnc-password.txt")
    subprocess.run(["x11vnc", "-storepasswd", vnc[:8], str(runtime / "vnc.auth")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if rustdesk:
        directory = config / "rustdesk"
        directory.mkdir(parents=True, exist_ok=True)
        saved = directory / "connection-password.txt"
        auth = directory / "RustDesk.toml"
        # Keep RustDesk's rewritten identity and credentials on subsequent starts.
        if not auth.exists() or os.environ.get("RUSTDESK_PASSWORD") is not None or os.environ.get("RUSTDESK_PASSWORD_FILE"):
            value = password("RUSTDESK_PASSWORD", saved)
            if auth.exists():
                import re
                text = auth.read_text()
                line = "password = " + json.dumps(value)
                text, count = re.subn(r"^password\s*=.*$", lambda _: line, text, count=1, flags=re.M)
                if not count:
                    text = line + "\n" + text
                auth.write_text(text)
            else:
                auth.write_text("password = " + json.dumps(value) + "\n")
            auth.chmod(0o600)
        options = directory / "RustDesk2.toml"
        if not options.exists():
            options.write_text('[options]\napprove-mode = "password"\nverification-method = "use-permanent-password"\ndirect-server = "Y"\n')
        print(f"RustDesk password file: {saved}")
    (runtime / "flags").write_text(f"ENABLE_RUSTDESK={'true' if rustdesk else 'false'}\nENABLE_CDP={'true' if cdp else 'false'}\n")
    print(f"VNC password file: {config / 'vnc-password.txt'} (VNC uses the first 8 characters)")


if __name__ == "__main__":
    main()
