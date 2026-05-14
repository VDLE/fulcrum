# Handle all screen recording of trials


import mss
import cv2
import numpy as np
import time
import os
import subprocess
import threading
from tracking.utility.file_management import get_file_path
from tracking.utility.capabilities import supported_measurements
from imageio_ffmpeg import get_ffmpeg_exe

ffmpeg_path = get_ffmpeg_exe()


# Global recording events
recording_stop = threading.Event()
recording_active = threading.Event()
adjustments_finished = threading.Event()


def record_screen(dir_output_base):
    recording_stop.clear()
    adjustments_finished.clear()
    recording_active.set()

    # /run_study already rejects sessions whose measurement set isn't
    # supported, but guard here too so a direct call doesn't hang.
    if "Screen Recording" not in supported_measurements():
        print(
            "[record_screen] Screen Recording not supported on this platform; "
            "skipping (this trial will not have an .mp4)"
        )
        adjustments_finished.set()
        recording_active.clear()
        return

    file_path = get_file_path(dir_output_base, "Screen Recording", "mp4")
    temp_fps = 15
    delay = 1 / temp_fps

    out = None
    frame_count = 0
    start_time = time.time()
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            codec = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(
                file_path, codec, temp_fps, (monitor["width"], monitor["height"])
            )
            next_frame_time = start_time
            while not recording_stop.is_set():
                curr_time = time.time()
                if curr_time >= next_frame_time:
                    image = sct.grab(monitor)
                    frame = np.array(image)[:, :, :3]
                    out.write(frame)
                    frame_count += 1
                    next_frame_time += delay
                else:
                    time.sleep(0.001)
    except Exception as e:
        # wait_trial_save() in driver.py spins on adjustments_finished. If we
        # raise without setting it the participant gets stuck on the "Saving
        # results..." modal until they force-quit.
        print(f"[record_screen] capture failed: {e!r}; continuing without recording")
        adjustments_finished.set()
        return
    finally:
        if out is not None:
            out.release()
        cv2.destroyAllWindows()
        recording_active.clear()

    if frame_count > 0:
        time_elapsed = time.time() - start_time
        fps = frame_count / time_elapsed
        adjuster_thread = threading.Thread(
            target=adjust_video, args=(file_path, fps), daemon=True
        )
        adjuster_thread.start()
    else:
        adjustments_finished.set()


# Need this function because fps varies for each person so we have to correct the video using calculated fps using ffmpeg or else play speed and video length will be incorrect
def adjust_video(f_path, fps):
    temp_f_path = f_path.replace(".mp4", "_temp.mp4")

    # Ref FFmpeg https://trac.ffmpeg.org/wiki/How%20to%20speed%20up%20/%20slow%20down%20a%20video
    command = [
        ffmpeg_path,
        "-y",
        "-i",
        f_path,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-vf",
        f"setpts={15 / fps}*PTS",
        temp_f_path,
    ]

    subprocess.run(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )  # stop FFmpeg terminal output details

    if os.path.exists(temp_f_path):
        os.replace(temp_f_path, f_path)

    adjustments_finished.set()
