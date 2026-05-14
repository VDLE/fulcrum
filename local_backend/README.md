# Fulcrum Tracking Tool (local agent)

A PyQt6 desktop app that captures mouse, keyboard, screen, and heatmap data on
the participant's machine and hands the results off to the Fulcrum web app via
the participant's browser.

Distributed as Python source, not a precompiled binary. Participants install
Python and run the script.

## Prerequisites

- Python 3.10 to 3.12 (3.12 recommended; later versions currently lack prebuilt wheels
  for some of the pinned dependencies).
- A working desktop session. The tool is a GUI app and will not run headless.

## Install (all platforms)

```bash
git clone <fulcrum repo>
cd local_backend

python -m venv .venv
# Linux / macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
python driver.py
```

On startup the tracker prints a Werkzeug `Running on http://127.0.0.1:5001`
banner and shows a small "Ready to Go!" dialog. Click Continue, then drive the
rest of the session from the Fulcrum web app.

Sessions are staged at:

| OS | Path |
|---|---|
| Windows | `C:\Users\<user>\AppData\Local\Fulcrum\sessions\` |
| macOS | `~/Library/Application Support/Fulcrum/sessions/` |
| Linux | `~/.local/share/Fulcrum/sessions/` |

Override with `FULCRUM_STORAGE_DIR=/some/path python driver.py` if you want
the local copy somewhere specific.

## Per-platform notes

### Windows 10 / 11
Works out of the box. On first launch Windows Defender may prompt about the
input listener; allow it.

### macOS 12+
Grant two one-time permissions in **System Settings > Privacy & Security**:

1. Accessibility for mouse and keyboard event capture. Add your Python
   interpreter, or the Terminal/iTerm running it.
2. Screen Recording for Heat Map and Screen Recording measurements. Same
   target.

The tracker prints reminders to stderr on startup. Restart the tracker after
granting permissions.

### Linux + X11 (Ubuntu Xorg, Fedora KDE Xorg, etc.)
PyQt6's xcb platform plugin needs one system package:

```bash
# Debian / Ubuntu
sudo apt install libxcb-cursor0

# Fedora / RHEL
sudo dnf install xcb-util-cursor
```

Without it the agent aborts at startup with:

```
qt.qpa.plugin: From 6.5.0, xcb-cursor0 or libxcb-cursor0 is needed to
load the Qt xcb platform plugin.
```

### Linux + Wayland (NOT SUPPORTED)
The agent refuses to start any session on a Wayland host. Reasons:

- pynput's Linux backend uses python-xlib and only sees events that reach
  Xwayland's X server. Native Wayland apps (Firefox under Wayland, GNOME
  apps, KDE Wayland apps, etc.) bypass Xwayland, so input listeners record
  empty CSVs.
- Screen capture has the same problem. mss and PIL.ImageGrab both use X11
  capture APIs that cannot see native Wayland surfaces.

Fix: log out of the Wayland session and choose an X11/Xorg variant at the
login screen (e.g., "Ubuntu on Xorg") before launching the tracker. The agent
prints a banner and shows a Qt error dialog when it starts under Wayland; the
website will also refuse to start any session with a matching banner.

## Troubleshooting

**Connection refused on http://127.0.0.1:5001/check_local_tracking_running**  
The tracker isn't running, or its embedded Flask server crashed. Check the
terminal where you ran `python driver.py`; exceptions in the Flask thread
are printed there.

**The Begin button doesn't start the trial (browser shows an error banner)**  
The study's measurement list includes something the participant's platform
can't do. The exact reason is in the banner. Most often it's a Wayland
session; see the section above.

**Trial ends but "Saving results..." dialog hangs forever**  
You're probably running an older version of the agent. Re-download the
tracker ZIP from the Fulcrum web app.
