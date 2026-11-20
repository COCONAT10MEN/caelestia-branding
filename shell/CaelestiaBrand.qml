pragma Singleton
// caelestia-branding:managed
// Installed into the shell by the Caelestia Branding plugin
// (https://github.com/COCONAT10MEN/caelestia-branding) and removed by its
// revert. Inert while the plugin is not running, so disabling the plugin
// shows the stock "Nexus" wording again.

import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    // Set by the plugin while it is loaded.
    property bool active: false

    // The product name exactly as the shell's own About page shows it, read
    // from that page so it follows Caelestia if the name ever changes.
    property string fullName: "Caelestia KDE"
    // What the user sees instead of "Nexus": the name without the platform suffix.
    readonly property string name: root.fullName.replace(/\s+KDE$/i, "").trim() || "Caelestia"

    /// User-visible text with "Nexus" replaced by Caelestia's name. Applied to
    /// the already-translated string, so translations keep working.
    function rename(text: string): string {
        return root.active ? String(text).replace(/\bNexus\b/g, root.name) : text;
    }

    FileView {
        path: Quickshell.shellPath("modules/nexus/pages/AboutPage.qml")
        watchChanges: true
        printErrors: false

        onFileChanged: reload()
        onLoaded: {
            // The headline under the About page's animated logo.
            const m = /AnimatedLogo\s*\{[\s\S]*?\}\s*StyledText\s*\{[^}]*?\btext:\s*"([^"]+)"/.exec(text());
            if (m && m[1].trim().length > 0)
                root.fullName = m[1].trim();
        }
    }
}
