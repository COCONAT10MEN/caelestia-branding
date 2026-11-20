# Caelestia Branding

> ✅ **Tested and working on Caelestia KDE 2.7.5.**
> Other versions may work too; if an update changes the code this plugin hooks
> into, it switches itself off safely (see *How it works*) and a notification
> tells you.

A [Caelestia](https://github.com/caelestia-kde) plugin that shows Caelestia's
own name and logo wherever you would otherwise see **"Nexus"** or the
**noctalia-qs moon icon**.

## What changes

| Where | Before | After |
| --- | --- | --- |
| Titlebar, taskbar, Alt+Tab icon of the shell's windows (settings, editors…) | noctalia-qs moon | Caelestia logo, **in your current theme colours** |
| Their app name in KDE | noctalia-qs | Caelestia |
| Settings → Appearance → "Nexus settings" (list, page title, search) | Nexus settings | Caelestia settings |
| The settings window's title before a page is chosen | Nexus | Caelestia |
| This plugin's icon in the Plugins list | — | the themed Caelestia logo |

Nothing is recreated or hard-coded:

- **Logo:** rendered by Caelestia's own `Logo` component (the logo on the
  bar) in whatever colour theme you use, and re-rendered automatically every
  time your colours change.
- **Name:** read from Caelestia's About page ("Caelestia KDE"), shown as
  "Caelestia". If Caelestia renames itself, this follows.
- Translations keep working: only the word "Nexus" is swapped inside the
  already-translated text.

## Install

Settings → Plugins → install from URL, paste:

```
https://github.com/COCONAT10MEN/caelestia-branding
```

Needs `python3`. On first start the plugin hooks into the shell and restarts
it once. Windows that were already open may keep the old icon until reopened.

## How it works

- **KDE side.** Caelestia's windows identify as the app
  `dev.noctalia.noctalia-qs` (the Quickshell build Caelestia runs on), so KDE
  shows that app's name and icon. The plugin writes a user-level override,
  `~/.local/share/applications/dev.noctalia.noctalia-qs.desktop`, with
  Caelestia's name and the rendered logo
  (`~/.local/share/caelestia/branding/caelestia-logo-*.png`). Nothing
  system-wide is touched, and it never overwrites an entry someone else made.
- **Shell side.** Caelestia's plugin API has no hook for this, so on every
  shell start `patch.py` adds a small `services/CaelestiaBrand.qml` and wraps
  the few user-visible "Nexus" strings. Every change is wrapped in
  `// caelestia-branding:begin … :end` markers that store the original text, so
  a revert restores the files byte for byte. After a Caelestia update it
  patches again and restarts the shell once (through its `caelestia-shell`
  systemd service). If an update changed that code, **every** file goes back to
  stock (never half-patched) and a notification tells you.
- While the plugin is disabled, the hooks do nothing and the wording is stock.
- The dock still refuses "End task" on the settings window, so it can't kill
  the shell.

## Uninstall

```bash
python3 ~/.config/caelestia/plugins/caelestia-branding/patch.py revert ~/.config/quickshell/caelestia
python3 ~/.config/caelestia/plugins/caelestia-branding/brand-desktop.py revert
rm -rf ~/.local/share/caelestia/branding
```

Then remove the plugin in Settings → Plugins and restart the shell.

## License

[MIT](LICENSE): free for anyone to use, modify and redistribute, including in
other plugins or commercial projects. The only ask: if you use this as a base,
credit **[COCONAT10MEN](https://github.com/COCONAT10MEN)** (keeping the
LICENSE file's copyright line does that).
