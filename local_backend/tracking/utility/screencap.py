"""Single-frame screen capture for the Fulcrum tracking agent.

Windows / macOS / Linux+X11 all use PIL.ImageGrab (native backend per OS).
Wayland is not supported by the agent (see capabilities.py); validation
rejects every Wayland session up front, so we never reach take_screenshot
on a Wayland host.
"""

from PIL import ImageGrab


def take_screenshot(out_path):
    """Capture the whole screen to `out_path`. Returns True on success."""
    try:
        ImageGrab.grab().save(out_path)
        return True
    except Exception as e:
        print(f"[screencap] ImageGrab failed: {e!r}")
        return False
