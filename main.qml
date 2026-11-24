import QtQuick
import Quickshell
import Quickshell.Io
import Caelestia
import qs.components
import qs.services
import "updater"

// Caelestia Branding: everywhere the user sees "Nexus" (and the noctalia-qs
// app identity KDE shows for the shell's windows), show Caelestia's own name
// and logo instead, both read live from Caelestia itself.
Scope {
    id: root

    readonly property string pluginDir: decodeURIComponent(Qt.resolvedUrl(".").toString().replace(/^file:\/\//, "")).replace(/\/$/, "")
    readonly property string iconDir: (Quickshell.env("XDG_DATA_HOME") || (Quickshell.env("HOME") + "/.local/share")) + "/caelestia/branding"

    // False only on the first start after install or a Caelestia update,
    // before patch.py has added the shell side; the shell restarts right after.
    readonly property bool shellReady: typeof CaelestiaBrand !== "undefined"
    readonly property string brandName: root.shellReady ? CaelestiaBrand.name : ""

    // ============================================================== logo

    // The app icon is the shell's own Logo component (the logo on the bar),
    // rendered in the current theme colours, never redrawn by this plugin.
    // It is re-rendered whenever the colours change, under a new file name so
    // KDE does not keep showing a cached old one.
    readonly property string logoColours: [Colours.palette.m3primary, Colours.palette.m3onSurface, Colours.palette.m3onPrimary, Colours.palette.m3surface].map(c => c.toString()).join("|")
    property string iconFile: ""
    property var grabHost: null
    // Grab attempts for the current colours; after a few the stock icon is used.
    property int grabTries: 0
    readonly property bool renderPending: root.iconFile === "" && root.grabTries < 8

    function colourKey(): string {
        let h = 0;
        for (const ch of root.logoColours)
            h = (h * 31 + ch.charCodeAt(0)) >>> 0;
        return h.toString(16);
    }

    /// Any item inside one of the shell's visible windows works as a host:
    /// the logo is created in a zero-size clipped box, so it is never seen.
    function findHost(): var {
        for (const bar of Visibilities.bars.values())
            if (bar)
                return bar;
        return null;
    }

    function renderLogo(): void {
        if (!root.grabHost) {
            const host = root.findHost();
            if (!host) {
                renderRetry.restart();
                return;
            }
            root.grabHost = Qt.createQmlObject(`
                import QtQuick
                import qs.components
                Item {
                    width: 0
                    height: 0
                    clip: true
                    property alias logo: logo
                    Logo {
                        id: logo
                        width: 256
                        height: 256
                    }
                }`, host, "caelestiaBrandingLogo");
        }
        const out = root.iconDir + "/caelestia-logo-" + root.colourKey() + ".png";
        root.grabTries++;
        // Let the new colours reach the logo before grabbing it. A grab fails
        // quietly while the bar's window is still being shown, so a watchdog
        // tries again until it works.
        grabWatchdog.restart();
        Qt.callLater(() => {
            const started = root.grabHost.logo.grabToImage(result => {
                grabWatchdog.stop();
                if (!result.saveToFile(out)) {
                    console.warn("[caelestia-branding] could not save the logo to " + out);
                    return;
                }
                root.grabTries = 0;
                root.iconFile = out;
                // Old renders and the plugin's own Nexus icon.
                Quickshell.execDetached(["sh", "-c", 'for f in "$1"/caelestia-logo-*.png; do [ "$f" = "$2" ] || rm -f "$f"; done; cp -f "$2" "$3"', "--", root.iconDir, out, root.pluginDir + "/icon.png"]);
                root.brandKde();
            }, Qt.size(256, 256));
            if (!started) {
                grabWatchdog.stop();
                root.retryRender();
            }
        });
    }

    function retryRender(): void {
        if (root.grabTries < 8) {
            renderRetry.restart();
        } else if (!root.iconFile) {
            console.warn("[caelestia-branding] could not render the logo; using Caelestia's stock icon");
            root.brandKde();
        }
    }

    Timer {
        id: grabWatchdog

        interval: 3000
        onTriggered: root.retryRender()
    }

    /// The last render for these colours, if there is one, works right away.
    Process {
        id: lastRender

        stdout: StdioCollector {
            onStreamFinished: {
                const p = text.trim();
                if (p && !root.iconFile) {
                    root.iconFile = p;
                    root.brandKde();
                }
            }
        }
    }

    onLogoColoursChanged: {
        root.grabTries = 0;
        renderDebounce.restart();
    }

    Timer {
        id: renderDebounce

        interval: 1200
        onTriggered: root.renderLogo()
    }

    Timer {
        id: renderRetry

        interval: 1000
        onTriggered: root.renderLogo()
    }

    Process {
        id: mkdir

        command: ["mkdir", "-p", root.iconDir]
        onExited: {
            lastRender.command = ["sh", "-c", 'f="$1/caelestia-logo-$2.png"; [ -s "$f" ] && echo "$f"', "--", root.iconDir, root.colourKey()];
            lastRender.running = true;
            root.renderLogo();
        }
    }

    // ======================================================= KDE identity

    // Titlebar/taskbar/Alt+Tab name and icon for the shell's windows.
    function brandKde(): void {
        // Wait for the themed logo rather than showing the stock icon first.
        if (root.renderPending)
            return;
        if (!root.brandName || desktopProc.running) {
            if (root.brandName)
                kdeRetry.restart();
            return;
        }
        desktopProc.command = ["python3", "-I", root.pluginDir + "/brand-desktop.py", "apply", root.brandName, root.iconFile];
        desktopProc.running = true;
    }

    onBrandNameChanged: brandKde()

    Timer {
        id: kdeRetry

        interval: 500
        onTriggered: root.brandKde()
    }

    Process {
        id: desktopProc

        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const r = JSON.parse(text);
                    if (!r.ok)
                        console.warn("[caelestia-branding] " + r.error);
                    else if (r.changed)
                        console.info("[caelestia-branding] KDE now shows \"" + r.name + "\" with icon " + r.icon + " for " + r.written.join(", "));
                } catch (e) {
                    console.warn("[caelestia-branding] brand-desktop.py: " + text);
                }
            }
        }
    }

    Component.onCompleted: {
        if (!root.shellReady)
            return;
        CaelestiaBrand.active = true;
        mkdir.running = true;
    }

    Component.onDestruction: {
        if (root.grabHost)
            root.grabHost.destroy();
        if (root.shellReady)
            CaelestiaBrand.active = false;
    }

    // ========================================================== patching

    // Restart the shell process (via its systemd service) instead of an
    // in-process reload, which can deadlock and does not restart plugins.
    function restartShell(): void {
        Quickshell.execDetached(["sh", root.pluginDir + "/restart-shell.sh", Quickshell.shellPath("shell.qml")]);
    }

    function handle(output: string): void {
        const result = output.trim();
        if (result === "PATCHED") {
            console.info("[caelestia-branding] patched the shell, restarting it");
            root.restartShell();
        } else if (result === "OK") {
            console.info("[caelestia-branding] patch already in place");
        } else {
            console.warn("[caelestia-branding] " + result);
            Toaster.toast(qsTr("Caelestia Branding"), qsTr("Caelestia changed in its last update, so this is off for now. Checking for a fix..."), "warning");
            updater.checkNow();
            if (result.startsWith("FAILED+RELOAD"))
                root.restartShell();
        }
    }

    Process {
        running: true
        command: ["python3", "-I", root.pluginDir + "/patch.py", "apply", Quickshell.shellDir]
        stdout: StdioCollector {
            onStreamFinished: root.handle(text)
        }
    }

    // Opt-in updates: asks before changing anything (see updater/update.sh).
    Updater {
        id: updater

        pluginDir: root.pluginDir
    }
}
