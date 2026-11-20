#!/usr/bin/env python3
"""KDE-side branding for Caelestia's windows.

Caelestia runs on a Quickshell build whose windows identify as their own app
(for example dev.noctalia.noctalia-qs), so KDE's titlebar, taskbar and Alt+Tab
show that app's name and icon. This writes a user-level override of that app
entry with Caelestia's own name and icon; nothing system-wide is touched.

The icon is the image the plugin renders from the shell's own Logo component
(the logo on the bar, in the current theme colours). Without one, Caelestia's
own app icon (Icon=caelestia from org.quickshell.desktop) is used by name.

    brand-desktop.py apply NAME [ICON_FILE]  write/refresh the overrides
    brand-desktop.py revert                  remove them
Prints one JSON object.
"""

import json
import os
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
DATA_HOME = os.environ.get("XDG_DATA_HOME") or os.path.join(HOME, ".local/share")
DATA_DIRS = [d for d in (os.environ.get("XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":") if d]
USER_APPS = os.path.join(DATA_HOME, "applications")
MARK = "X-Caelestia-Branding"
# App ids Quickshell builds give their windows.
CANDIDATES = ["dev.noctalia.noctalia-qs", "org.quickshell", "quickshell"]
CAELESTIA_ENTRY = os.path.join(USER_APPS, "org.quickshell.desktop")


def read_group(path):
    out, cur = [], None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f.read().splitlines():
            s = line.strip()
            if s.startswith("[") and s.endswith("]"):
                cur = s[1:-1]
                continue
            if cur == "Desktop Entry" and "=" in s and not s.startswith("#"):
                k, v = s.split("=", 1)
                out.append((k.strip(), v.strip()))
    return out


def value(path, key):
    try:
        for k, v in read_group(path):
            if k == key:
                return v
    except OSError:
        pass
    return None


def system_entry(app_id):
    for d in DATA_DIRS:
        p = os.path.join(d, "applications", app_id + ".desktop")
        if os.path.exists(p):
            return p
    return None


def caelestia_icon():
    """The icon Caelestia gives its own windows."""
    return value(CAELESTIA_ENTRY, "Icon") or "caelestia"




def rebuild():
    exe = shutil.which("kbuildsycoca6") or shutil.which("kbuildsycoca5")
    if exe:
        subprocess.Popen([exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def apply(name, icon_file):
    icon = icon_file if icon_file and os.path.exists(icon_file) else caelestia_icon()
    changed, written, skipped = False, [], []
    for app_id in CANDIDATES:
        sys_path = system_entry(app_id)
        user_path = os.path.join(USER_APPS, app_id + ".desktop")
        if not sys_path:
            continue
        if os.path.exists(user_path) and value(user_path, MARK) is None:
            skipped.append(app_id)  # someone else's override (e.g. Caelestia's own): leave it
            continue
        keys = [(k, v) for k, v in read_group(sys_path) if not k.startswith("Name") and k != "Icon" and k != MARK]
        lines = ["[Desktop Entry]", f"Name={name}", f"Icon={icon}"] + [f"{k}={v}" for k, v in keys] + [f"{MARK}=true", ""]
        text = "# Managed by the Caelestia Branding plugin; removed by its revert.\n" + "\n".join(lines)
        old = None
        if os.path.exists(user_path):
            with open(user_path, encoding="utf-8", errors="replace") as f:
                old = f.read()
        if old != text:
            os.makedirs(USER_APPS, exist_ok=True)
            tmp = user_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(text)
            os.replace(tmp, user_path)
            changed = True
        written.append(app_id)
    if changed:
        rebuild()
    return {"ok": True, "name": name, "icon": icon, "written": written, "skipped": skipped, "changed": changed}


def revert():
    removed = []
    for app_id in CANDIDATES:
        p = os.path.join(USER_APPS, app_id + ".desktop")
        if os.path.exists(p) and value(p, MARK) is not None:
            os.unlink(p)
            removed.append(app_id)
    if removed:
        rebuild()
    return {"ok": True, "removed": removed}


def main(argv):
    try:
        if len(argv) >= 3 and argv[1] == "apply":
            res = apply(argv[2].strip() or "Caelestia", argv[3] if len(argv) > 3 else "")
        elif len(argv) == 2 and argv[1] == "revert":
            res = revert()
        else:
            res = {"ok": False, "error": "usage: apply NAME [PLUGIN_DIR] | revert"}
    except Exception as e:
        res = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    print(json.dumps(res))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
