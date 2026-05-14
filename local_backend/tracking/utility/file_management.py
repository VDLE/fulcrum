# Purpose: All functionalities for producing csvs and zips


import os
import pandas as pd
import zipfile
import shutil  # used to remove folder once zip is created


# Returns the path to a directory for a session or trial depending on what parameters are passed
def get_save_dir(storage_path, sess_id, task=None, factor=None, trial_num=None):
    # path to session folder
    dir_session = os.path.join(storage_path, f"Session_{sess_id}")

    if task is None or factor is None:
        return dir_session

    # path to trial folder
    task_name = task["taskName"]
    factor_name = factor["factorName"]

    dir_trial = os.path.join(
        dir_session, f"{task_name}_{factor_name}_trial_{trial_num}"
    )

    return dir_trial


# Constructs the full file path and enforces a naming convention
def get_file_path(dir_trial, measurement_type, file_format):
    file_name = f"{measurement_type}.{file_format}"
    full_path = os.path.join(dir_trial, file_name)

    return full_path


# Generating a unique csv based on the measurement type during a given trial
def write_to_csv(measurement_type, feature, arr_data, is_used, task, dir_trial):
    if not is_used:
        return

    file_path = get_file_path(dir_trial, measurement_type, "csv")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Prevent writing values that exceeded task duration due to delay between signaling task end and stopping tracking threads
    task_dur = task.get("taskDuration")
    if task_dur is not None:
        time_cutoff = float(task_dur) * 60
    else:
        time_cutoff = float("inf")
    updated_data = [row for row in arr_data if float(row[1]) <= time_cutoff]

    # Convert to df
    if feature == "mouse":
        df = pd.DataFrame(updated_data, columns=["Time", "running_time", "x", "y"])

    elif feature == "keyboard":
        df = pd.DataFrame(updated_data, columns=["Time", "running_time", "keys"])

    # Unique behavior for mouse movement CSVs because we did batch writes
    if os.path.exists(
        file_path
    ):  # CSV already exists so we just append and don't add headers
        df.to_csv(file_path, mode="a", header=False, index=False)
    else:  # CSV does not exist so have to create and add headers
        df.to_csv(file_path, index=False)


# Packages a folder containing all session data into a zip file
def package_session_results(session_id, storage_path):
    dir_session = get_save_dir(storage_path, session_id)
    zip_path = os.path.join(storage_path, f"session_results_{session_id}.zip")
    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for trial_folder in os.listdir(dir_session):
                trial_path = os.path.join(dir_session, trial_folder)
                if os.path.isdir(trial_path):
                    # Empty trial folders (user used alt methods for collecting data) must still be included in zip
                    if not os.listdir(trial_path):
                        arcname = os.path.relpath(trial_path, dir_session) + "/"
                        zip_info = zipfile.ZipInfo(arcname)
                        zipf.writestr(zip_info, "")
                    else:
                        for root, _, files in os.walk(trial_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, dir_session)
                                zipf.write(file_path, arcname)

        shutil.rmtree(dir_session)
        print(f"Session {session_id} results saved to {zip_path}!")

    except Exception as e:
        print(f"Error occured while trying to package session {session_id}: {e}")
