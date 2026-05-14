# Purpose: Holds all functions related to generating heatmaps for mouse movement


import os
import time
import csv
import cv2
import numpy as np
import threading
from tracking.utility.file_management import get_file_path
from tracking.utility.screencap import take_screenshot


# Used to signal heatmap gen is complete
heatmap_generation_complete = threading.Event()


def generate_heatmap(dir_trial):
    # wait_trial_save() in driver.py blocks on heatmap_generation_complete.
    # Set it in finally so a crash here never deadlocks the trial.
    screenshot_path = get_file_path(dir_trial, "screenshot", "png")
    try:
        if not take_screenshot(screenshot_path):
            print(
                "[generate_heatmap] screen capture unavailable; "
                "skipping heatmap (other measurements still collected)"
            )
            return

        screenshot = cv2.imread(screenshot_path)
        mouse_data_path = get_file_path(dir_trial, "Mouse Movement", "csv")
        coordinates = extract_mouse_movements(mouse_data_path)

        if coordinates:
            heatmap = create_heatmap(coordinates, screenshot.shape)
            overlay = overlay_heatmap(heatmap, screenshot)
            heatmap_path = get_file_path(dir_trial, "Heat Map", "png")
            cv2.imwrite(heatmap_path, overlay)
            time.sleep(1)
    except Exception as e:
        print(f"[generate_heatmap] failed: {e!r}; skipping heatmap")
    finally:
        # Always remove the intermediate screenshot.png. The backend upload
        # loop treats every file in a trial folder as a measurement, so a
        # leftover "screenshot.png" rolls back the whole session with
        # 'No measurement option found for screenshot'.
        try:
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
        except OSError as e:
            print(f"[generate_heatmap] failed to clean up screenshot: {e!r}")
        heatmap_generation_complete.set()


def extract_mouse_movements(log_file):
    coordinates = []
    with open(log_file, "r") as f:
        reader = csv.reader(f)
        next(reader)  # skips the header
        for row in reader:
            x, y = int(row[2]), int(row[3])
            coordinates.append((x, y))

    return coordinates


def create_heatmap(coordinates, screenshot_shape):
    heatmap = np.zeros(screenshot_shape[:2], dtype=np.float32)

    for x, y in coordinates:
        if 0 <= x < screenshot_shape[1] and 0 <= y < screenshot_shape[0]:
            heatmap[y, x] += 1

    # Apply Gaussian blur to smooth the heatmap
    heatmap = cv2.GaussianBlur(heatmap, (15, 15), 0)

    return heatmap


def overlay_heatmap(heatmap, screenshot):
    heatmap_normalized = cv2.normalize(heatmap, None, 0, 255, cv2.NORM_MINMAX)
    heatmap_colored = cv2.applyColorMap(
        heatmap_normalized.astype(np.uint8), cv2.COLORMAP_JET
    )

    # Combine the heatmap with the original screenshot
    overlay = cv2.addWeighted(screenshot, 0.7, heatmap_colored, 0.3, 0)

    return overlay
