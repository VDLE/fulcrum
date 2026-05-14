# Purpose: Construct a unit test for screen recording functionality, making sure it saves properly to intended location


import os
import sys
import time
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from tracking.utility.screenrecording import record_screen, recording_stop


def test_screen_recording():
    output_loc = os.path.expanduser(
        "~"
    )  # For testing purposes we will be saving to user's home dir
    filename = "sample"
    test_duration = 300  # In seconds but can test longer length videos if needed

    # Have to use threading since that is how screen recording is setup to run, using events to trigger stop
    recording_thread = threading.Thread(
        target=record_screen, args=(output_loc, filename)
    )
    recording_thread.start()

    # Allows us to stress test by running unit test with variable lengths
    time.sleep(test_duration)

    recording_stop.set()
    recording_thread.join()

    file_path = os.path.join(output_loc, f"{filename}_screen_recording.mp4")
    assert (
        os.path.exists(file_path) == True
    ), f"Sample screen recording failed to generate at {file_path}"

    os.remove(file_path)  # Cleans up the generated sample recording


if __name__ == "__main__":
    test_screen_recording()
