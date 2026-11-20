#!/usr/bin/env python3
"""Caelestia Branding patcher.

Swaps the word "Nexus" the user sees for Caelestia's own name (read at run
time from the shell's About page) via a CaelestiaBrand singleton. Caelestia's
plugin API has no hook for this, so this script:

* copies shell/CaelestiaBrand.qml into services/
* wraps the few user-visible "Nexus" strings in CaelestiaBrand.rename()

Every change is wrapped in marker comments that store the original text
(base64), so `revert` restores the files byte for byte. The plugin runs
`apply` on every shell start, so updates are re-patched; if a snippet no
longer matches, every file goes back to stock instead of half-patched.

Usage:
    patch.py apply  <shell dir>  -> OK | PATCHED | FAILED[+RELOAD]: <reason>
    patch.py revert <shell dir>  -> REVERTED | NOTHING
    patch.py status <shell dir>  -> APPLIED | PARTIAL | MISSING
"""

import base64
import os
import re
import sys
import tempfile

TAG = "caelestia-branding"
VERSION = "1"
HERE = os.path.dirname(os.path.abspath(__file__))
MANAGED = f"// {TAG}:managed"
CREATED = {
    "services/CaelestiaBrand.qml": os.path.join(HERE, "shell", "CaelestiaBrand.qml"),
}
BLOCK_RE = re.compile(
    r"^// " + TAG + r":begin[^\n]*\n.*?^// " + TAG + r":orig ([A-Za-z0-9+/=]*)\n// " + TAG + r":end\n",
    re.S | re.M,
)

# (file, exact original snippet, replacement). Snippets are whole lines.
OPS = [
    # Nexus settings page entry (label, section, description)
    (
        "modules/nexus/PageCompRegistry.qml",
        '                label: qsTr("Nexus settings")\n'
        '                icon: "tune"\n'
        '                section: qsTr("Nexus")\n',
        '                label: CaelestiaBrand.rename(qsTr("Nexus settings"))\n'
        '                icon: "tune"\n'
        '                section: CaelestiaBrand.rename(qsTr("Nexus"))\n',
    ),
    (
        "modules/nexus/PageCompRegistry.qml",
        '                description: qsTr("Nexus window layout and subcategory side pane")\n',
        '                description: CaelestiaBrand.rename(qsTr("Nexus window layout and subcategory side pane"))\n',
    ),
    # Settings search index
    (
        "modules/nexus/PageRowIndex.qml",
        "import QtQuick\n",
        "import QtQuick\nimport qs.services\n",
    ),
    (
        "modules/nexus/PageRowIndex.qml",
        '            section: qsTr("Nexus settings"),\n',
        '            section: CaelestiaBrand.rename(qsTr("Nexus settings")),\n',
    ),
    # The settings page itself
    (
        "modules/nexus/pages/wallandstyle/NexusSettingsPage.qml",
        "import qs.modules.nexus.common\n",
        "import qs.modules.nexus.common\nimport qs.services\n",
    ),
    (
        "modules/nexus/pages/wallandstyle/NexusSettingsPage.qml",
        '    title: qsTr("Nexus settings")\n',
        '    title: CaelestiaBrand.rename(qsTr("Nexus settings"))\n',
    ),
    # Window title before a page is chosen
    (
        "modules/nexus/WindowFactory.qml",
        '            title: PageRegistry.pages[nexus.nState.currentPageIdx] ? PageRegistry.pages[nexus.nState.currentPageIdx].label : "Nexus"\n',
        '            title: PageRegistry.pages[nexus.nState.currentPageIdx] ? PageRegistry.pages[nexus.nState.currentPageIdx].label : CaelestiaBrand.rename("Nexus")\n',
    ),
    # The dock must keep refusing "End task" on the settings window (killing
    # it would kill the whole shell), now that its title can say Caelestia.
    (
        "modules/bar/popouts/DockContext.qml",
        '            return !model.toplevels.some(t => t.title && String(t.title).startsWith("Nexus"));\n',
        '            return !model.toplevels.some(t => t.title && (String(t.title).startsWith("Nexus") || (CaelestiaBrand.active && String(t.title).startsWith(CaelestiaBrand.name))));\n',
    ),
]


def block(original: str, replacement: str) -> str:
    b64 = base64.b64encode(original.encode()).decode()
    return f"// {TAG}:begin v{VERSION}\n{replacement}// {TAG}:orig {b64}\n// {TAG}:end\n"


def strip(text: str) -> str:
    return BLOCK_RE.sub(lambda m: base64.b64decode(m.group(1)).decode(), text)


def read(path: str):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_atomic(path: str, text: str) -> None:
    mode = os.stat(path).st_mode & 0o7777 if os.path.exists(path) else 0o644
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix="." + os.path.basename(path) + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# Files older versions patched and this one no longer does.
RETIRED_FILES = []


def plan(shell: str):
    """Current, stock and patched text of every touched file."""
    files = sorted({op[0] for op in OPS} | {f for f in RETIRED_FILES if os.path.exists(os.path.join(shell, f))})
    current = {}
    for rel in files:
        text = read(os.path.join(shell, rel))
        if text is None:
            raise FileNotFoundError(rel)
        current[rel] = text
    stock = {rel: strip(text) for rel, text in current.items()}
    return current, stock


def patched(stock: dict) -> dict:
    out = dict(stock)
    for rel, original, replacement in OPS:
        text = out[rel]
        count = text.count(original)
        if count != 1:
            first = original.strip().splitlines()[0].strip()
            raise ValueError(f"{rel}: snippet found {count} times: {first[:70]!r} (Caelestia changed; plugin needs updating)")
        out[rel] = text.replace(original, block(original, replacement), 1)
    return out


def created_state(shell: str):
    """[(dest, wanted text, current text or None, ours?)]"""
    res = []
    for rel, src in CREATED.items():
        with open(src, encoding="utf-8") as f:
            want = f.read()
        dest = os.path.join(shell, rel)
        cur = read(dest)
        res.append((dest, want, cur, cur is None or MANAGED in cur))
    return res


def remove_created(shell: str) -> bool:
    changed = False
    for dest, _want, cur, ours in created_state(shell):
        if cur is not None and ours:
            os.unlink(dest)
            changed = True
    return changed


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in ("apply", "revert", "status"):
        print(__doc__.strip())
        return 2
    action, shell = sys.argv[1], sys.argv[2]

    try:
        current, stock = plan(shell)
    except FileNotFoundError as e:
        print(f"FAILED: shell file missing: {e}")
        return 1

    if action == "status":
        n = sum(len(BLOCK_RE.findall(t)) for t in current.values())
        made = all(cur is not None and ours for _d, _w, cur, ours in created_state(shell))
        print("APPLIED" if n == len(OPS) and made else ("MISSING" if n == 0 and not made else "PARTIAL"))
        return 0

    if action == "revert":
        changed = False
        for rel, text in stock.items():
            if text != current[rel]:
                write_atomic(os.path.join(shell, rel), text)
                changed = True
        changed = remove_created(shell) or changed
        print("REVERTED" if changed else "NOTHING")
        return 0

    # apply
    try:
        want = patched(stock)
    except ValueError as e:
        # All-or-nothing: put everything back to stock so the shell stays sane.
        changed = False
        for rel, text in stock.items():
            if text != current[rel]:
                write_atomic(os.path.join(shell, rel), text)
                changed = True
        changed = remove_created(shell) or changed
        print(f"FAILED{'+RELOAD' if changed else ''}: {e}")
        return 1

    for dest, _w, cur, ours in created_state(shell):
        if cur is not None and not ours:
            print(f"FAILED: {dest} exists and is not ours; not touching it")
            return 1

    changed = False
    for dest, wanted, cur, _ours in created_state(shell):
        if cur != wanted:
            write_atomic(dest, wanted)
            changed = True
    for rel, text in want.items():
        if text != current[rel]:
            write_atomic(os.path.join(shell, rel), text)
            changed = True
    print("PATCHED" if changed else "OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
