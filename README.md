<div align="center">

<img src="https://raw.githubusercontent.com/caelestia-kde/caelestia/main/assets/caelestia.svg" width="80" alt="Caelestia logo" />

# caelestia-branding

[![Caelestia KDE](https://img.shields.io/badge/Caelestia_KDE-2.7.5_tested-9bd0cc?style=for-the-badge&labelColor=101418)](https://github.com/caelestia-kde/caelestia)
[![KDE Plasma](https://img.shields.io/badge/Plasma_6-1D99F3?logo=kde&logoColor=white&style=for-the-badge&labelColor=101418)](https://kde.org/plasma-desktop)
[![Version](https://img.shields.io/badge/Version-1.1.0-9bd0cc?style=for-the-badge&labelColor=101418)](metadata.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-9bd0cc?style=for-the-badge&labelColor=101418)](LICENSE)

</div>

> [!NOTE]
> **Tested and working on Caelestia KDE 2.7.5.** Other versions may work too: if an
> update changes the code this plugin hooks into, it switches itself off safely and a
> notification tells you.

A plugin for [Caelestia KDE](https://github.com/caelestia-kde/caelestia) that shows
Caelestia's own name and logo on the settings app and in KDE's titlebar, taskbar and
Alt+Tab, instead of the stock placeholder name and the **noctalia-qs moon icon**.

## Installation

**Requirements:** Caelestia KDE (tested on 2.7.5), `python3`

Open *Settings*, go to *Plugins*, and install from this URL:

```
https://github.com/COCONAT10MEN/caelestia-branding
```

On first start the plugin hooks into the shell and restarts it once. Windows that were
already open may keep the old icon until you reopen them.

### Updating

From version 1.1.0 on, the plugin tells you when a new version is out, and never updates on
its own:

- About once a day it looks at this repository's
  [Releases](https://github.com/COCONAT10MEN/caelestia-branding/releases). Only releases are offered, never
  work-in-progress commits.
- When there is one, a notification says what changed and which Caelestia version it was
  tested on, with **Update**, **What's new** and **Skip this version**. Close it and it asks
  again in three days.
- If a release needs a newer Caelestia than yours, the notification says so and does not
  offer it until you update Caelestia.
- **Update** downloads that release, keeps your current version aside and restarts Caelestia.
  A notification then offers **Undo update**, which puts the previous version back (that
  release is then not offered again; newer ones are).

Installed before 1.1.0? Install from the same URL once more to get this. Your shell settings are untouched.

Every version, with what changed and what it was tested on, is on the
[Releases](https://github.com/COCONAT10MEN/caelestia-branding/releases) page.

Turn update checks off (delete the file to turn them back on):

```bash
mkdir -p ~/.local/state/caelestia/plugin-updates/caelestia-branding && touch ~/.local/state/caelestia/plugin-updates/caelestia-branding/off
```

Undo the last update later:

```bash
bash ~/.config/caelestia/plugins/caelestia-branding/updater/update.sh rollback ~/.config/caelestia/plugins/caelestia-branding ~/.config/quickshell/caelestia
```

### Uninstalling

```bash
python3 ~/.config/caelestia/plugins/caelestia-branding/patch.py revert ~/.config/quickshell/caelestia
python3 ~/.config/caelestia/plugins/caelestia-branding/brand-desktop.py revert
rm -rf ~/.local/share/caelestia/branding
```

Then remove the plugin in *Settings -> Plugins* and restart the shell.

## What it changes

| Where | Before | After |
| --- | --- | --- |
| Titlebar, taskbar and Alt+Tab icon of the shell's windows | noctalia-qs moon | Caelestia logo, in your theme colours |
| App name of those windows in KDE | noctalia-qs | Caelestia |
| *Appearance -> Nexus settings* (list, page title, search) | Nexus settings | Caelestia settings |
| Settings window title before a page is chosen | Nexus | Caelestia |
| This plugin's icon in the Plugins list | - | the themed Caelestia logo |

Nothing is recreated or hard-coded:

- **Logo** - rendered by Caelestia's own `Logo` component (the logo on the bar) in
  whatever colour theme you use, and re-rendered every time your colours change
- **Name** - read from Caelestia's About page ("Caelestia KDE"), shown as "Caelestia"
- **Translations** - only the word "Nexus" is swapped inside the already-translated text

## Configuring

Nothing to configure: enable the plugin and it follows your theme and Caelestia's name
on its own. Disabling it in *Settings -> Plugins* brings the stock wording back.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| A window still shows the moon icon | Close and reopen it; KDE keeps the icon a window was opened with |
| Taskbar icon looks outdated after a theme change | Wait a second for the re-render, then reopen the window |
| "Could not rename Nexus after an update" notification | Caelestia changed the hooked code; everything was put back to stock. Check for a plugin update |
| Want to see what it is doing | Run `caelestia shell -l` and look for `[caelestia-branding]` lines |

## How it works

- **KDE side** - Caelestia's windows identify as the app `dev.noctalia.noctalia-qs`
  (the Quickshell build Caelestia runs on), so KDE shows that app's name and icon.
  The plugin writes a user-level override,
  `~/.local/share/applications/dev.noctalia.noctalia-qs.desktop`, with Caelestia's name
  and the rendered logo (`~/.local/share/caelestia/branding/caelestia-logo-*.png`).
  Nothing system-wide is touched, and an entry someone else made is never overwritten.
- **Shell side** - Caelestia's plugin API has no hook for this, so on every shell start
  `patch.py` adds `services/CaelestiaBrand.qml` and wraps the few user-visible "Nexus"
  strings. Every change sits between `// caelestia-branding:begin` and `:end` markers
  that store the original text, so a revert restores the files byte for byte.
- **Updates** - after a Caelestia update it patches again and restarts the shell once,
  through its `caelestia-shell` systemd service. If an update changed that code, every
  file goes back to stock (never half-patched).
- **Safety** - the dock still refuses *End task* on the settings window, so it can't
  kill the shell.

## Repository layout

```
main.qml              plugin entry: renders the logo, applies the patch, sets the KDE identity
brand-desktop.py      writes/reverts the KDE app entry override
patch.py              idempotent, revertible shell patcher
shell/                CaelestiaBrand.qml, the singleton patch.py installs into the shell
restart-shell.sh      restarts the shell through its systemd service
updater/              opt-in updates: update.sh (checks, asks, updates, undoes), Updater.qml
metadata.json         plugin manifest
```

## Credits

- [caelestia-kde](https://github.com/caelestia-kde/caelestia) by [ladybug-me](https://github.com/ladybug-me) and [0xSolanaceae](https://github.com/0xSolanaceae) - the shell, its logo and the plugin system this builds on
- [COCONAT10MEN](https://github.com/COCONAT10MEN) - this plugin

## License

MIT - see [LICENSE](LICENSE). Free for anyone to use, modify and redistribute, including
in other plugins or commercial projects. If you use this as a base, please credit
[COCONAT10MEN](https://github.com/COCONAT10MEN) (keeping the LICENSE file's copyright
line does that).
