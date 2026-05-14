"""Platform capability detection for the Fulcrum tracking agent.

`validate_measurements()` is the source of truth that the agent's
/run_study route consults before accepting a session.

Wayland is intentionally unsupported. pynput uses python-xlib and only sees
events from Xwayland's X server; native Wayland clients (Firefox/Chromium
under Wayland, GNOME apps, etc.) bypass Xwayland, which means input
listeners record empty CSVs. Screen capture has the same limitation.
"""

import os
import sys

PLATFORM_WINDOWS = "windows"
PLATFORM_MACOS = "macos"
PLATFORM_LINUX_X11 = "linux-x11"
PLATFORM_LINUX_WAYLAND = "linux-wayland"
PLATFORM_UNKNOWN = "unknown"


def detect_platform():
    if sys.platform.startswith("win"):
        return PLATFORM_WINDOWS
    if sys.platform == "darwin":
        return PLATFORM_MACOS
    if sys.platform.startswith("linux"):
        is_wayland = (
            os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
            or bool(os.environ.get("WAYLAND_DISPLAY"))
        )
        return PLATFORM_LINUX_WAYLAND if is_wayland else PLATFORM_LINUX_X11
    return PLATFORM_UNKNOWN


_FULL = {
    "Mouse Movement",
    "Mouse Scrolls",
    "Mouse Clicks",
    "Keyboard Inputs",
    "Screen Recording",
    "Heat Map",
}

_SUPPORTED = {
    PLATFORM_WINDOWS: _FULL,
    PLATFORM_MACOS: _FULL,
    PLATFORM_LINUX_X11: _FULL,
    # Wayland is intentionally empty; see module docstring.
    PLATFORM_LINUX_WAYLAND: set(),
    PLATFORM_UNKNOWN: set(),
}


def supported_measurements():
    return set(_SUPPORTED.get(detect_platform(), set()))


_WAYLAND_NOT_SUPPORTED_MESSAGE = (
    "This tracker does not support Linux Wayland sessions: input events from "
    "native Wayland windows are not visible to the agent, so trials would "
    "record empty data. Please log out and pick an X11/Xorg session at the "
    "login screen, then re-launch the tracker."
)


def validate_measurements(requested):
    """Return (ok, errors). `requested` may be any iterable of measurement names."""
    platform = detect_platform()
    if platform == PLATFORM_LINUX_WAYLAND:
        return False, [_WAYLAND_NOT_SUPPORTED_MESSAGE]

    requested = set(requested or [])
    supported = supported_measurements()
    unsupported = requested - supported
    if not unsupported:
        return True, []
    return False, [
        f"The following measurements are not supported on this platform "
        f"({platform}): {sorted(unsupported)}"
    ]
