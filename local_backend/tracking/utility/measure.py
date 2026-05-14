# Purpose: All functionality specific to the measurement mechanisms Fulcrum currently supports

import threading
import os
from pynput import keyboard, mouse
import time
from datetime import datetime
from tracking.utility.file_management import write_to_csv

# Global listeners
mouse_listener = None
key_listener = None
pause_event = threading.Event()
pause_event.set()
stop_event = threading.Event()
data_storage_complete_event = (
    threading.Event()
)  # prevent ending before data is written and stored

# Global storage
keyboard_data = []
mouse_move_data = []
mouse_click_data = []
mouse_scroll_data = []

# Global time variables
running_time = 0
paused_time = 0


#################### MOUSE FUNCTIONALITIES ####################

# Variables for reducing mouse movement pulling frequency by establishing a minimum pixel threshold before recording more data
THRESHOLD = 10
PREV_XPOS = 0
PREV_YPOS = 0
TIME_TRACKER = 0
curr_time = 0
prev_time = 0


def on_move(x, y, task, dir_trial):
    global PREV_XPOS, PREV_YPOS, curr_time, prev_time, running_time, mouse_move_data

    if not pause_event.is_set():  # ignore logging when paused
        return

    distance = euclidian_distance(x, y, PREV_XPOS, PREV_YPOS)
    curr_time = datetime.now().strftime("%H:%M:%S")

    # if the distance is larger than the threshold, then it can record
    if distance > THRESHOLD:  # and curr_time != prev_time:

        # inserts data into array
        mouse_move_data.append(
            [curr_time, "%.2f" % (time.time() - running_time - paused_time), x, y]
        )

        if (
            len(mouse_move_data) >= 250
        ):  # write in batch sizes of 250 to improve performance rather than at the end of a task when there may be tens of thousands of data points
            write_to_csv(
                "Mouse Movement",
                "mouse",
                mouse_move_data,
                "mouse",
                task,
                dir_trial,
            )
            mouse_move_data.clear()

        PREV_XPOS = x
        PREV_YPOS = y


def on_click(x, y, button, pressed):
    global running_time, mouse_click_data

    if not pause_event.is_set():  # ignore logging when paused
        return

    mouse_click_data.append(
        [
            datetime.now().strftime("%H:%M:%S"),
            "%.2f" % (time.time() - running_time - paused_time),
            x,
            y,
        ]
    )


def on_scroll(x, y, dx, dy):
    global running_time, mouse_scroll_data

    if not pause_event.is_set():  # ignore logging when paused
        return

    mouse_scroll_data.append(
        [
            datetime.now().strftime("%H:%M:%S"),
            "%.2f" % (time.time() - running_time - paused_time),
            x,
            y,
        ]
    )


def euclidian_distance(x1, y1, x2, y2):
    ed = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
    return ed


def stop_mouse_ps():
    global mouse_listener
    if mouse_listener is not None:
        mouse_listener.stop()
        mouse_listener = None


##############################################################


################## KEYBOARD FUNCTIONALITIES ##################


def on_press(key):
    global keyboard_data, running_time

    if not pause_event.is_set():  # ignore logging when paused
        return

    try:
        keyboard_data.append(
            [
                datetime.now().strftime("%H:%M:%S"),
                "%.2f" % (time.time() - running_time - paused_time),
                key.char,
            ]
        )
    except AttributeError:
        keyboard_data.append(
            [
                datetime.now().strftime("%H:%M:%S"),
                "%.2f" % (time.time() - running_time - paused_time),
                key,
            ]
        )


def stop_keyboard_ps():
    global key_listener
    if key_listener is not None:
        key_listener.stop()
        key_listener = None


##############################################################


#################### CORE FUNCTIONALITIES ####################


# Manages the actual data collection, using measurement flags to know what to collect for the current trial
def record_measurements(task, tracking_flags, dir_trial):
    global mouse_listener, key_listener, running_time, keyboard_data, running_time, paused_time, mouse_move_data, mouse_click_data, mouse_scroll_data

    running_time = time.time()
    paused_time = 0

    try:
        if mouse_listener is not None and mouse_listener.running:
            stop_mouse_ps()
        if key_listener is not None and mouse_listener.running:
            stop_keyboard_ps()

        def on_move_params(x, y):
            on_move(x, y, task, dir_trial)

        # Initialize mouse listener if needed
        if (
            tracking_flags.get("mouse_movement")
            or tracking_flags.get("mouse_clicks")
            or tracking_flags.get("mouse_scrolls")
        ):
            mouse_listener = mouse.Listener(
                on_move=on_move_params if tracking_flags["mouse_movement"] else None,
                on_click=on_click if tracking_flags["mouse_clicks"] else None,
                on_scroll=on_scroll if tracking_flags["mouse_scrolls"] else None,
            )

        # Initialize keyboard listener if needed
        if tracking_flags.get("keyboard_inputs"):
            key_listener = keyboard.Listener(
                on_press=on_press if tracking_flags["keyboard_inputs"] else None,
                on_release=None,
            )

        # Start listeners
        if mouse_listener:
            mouse_listener.start()
        if key_listener:
            key_listener.start()

        while not stop_event.is_set():
            time.sleep(0.1)

            if not pause_event.is_set():
                paused_time += 0.1
    finally:
        # Stop listeners after full duration run
        if mouse_listener:
            stop_mouse_ps()
        if key_listener:
            stop_keyboard_ps()

        # Writing before the current task ends
        write_to_csv(
            "Mouse Movement",
            "mouse",
            mouse_move_data,
            tracking_flags["mouse_movement"],
            task,
            dir_trial,
        )
        write_to_csv(
            "Keyboard Inputs",
            "keyboard",
            keyboard_data,
            tracking_flags["keyboard_inputs"],
            task,
            dir_trial,
        )
        write_to_csv(
            "Mouse Clicks",
            "mouse",
            mouse_click_data,
            tracking_flags["mouse_clicks"],
            task,
            dir_trial,
        )
        write_to_csv(
            "Mouse Scrolls",
            "mouse",
            mouse_scroll_data,
            tracking_flags["mouse_scrolls"],
            task,
            dir_trial,
        )

        # Resetting for next trial
        keyboard_data.clear()
        mouse_move_data.clear()
        mouse_click_data.clear()
        mouse_scroll_data.clear()

        data_storage_complete_event.set()


##############################################################
