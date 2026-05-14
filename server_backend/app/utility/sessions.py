import io
import shutil
import zipfile
import pandas as pd
import json
import os
import logging
from app.utility.db_connection import get_db_connection

# Configure logger
logger = logging.getLogger(__name__)


def process_trial_file(cur, conn, trial_id, participant_dir, trial_folder, file_name):
    # Full path
    data_instance_path = os.path.join(trial_folder, file_name)

    # Separate name (like Mouse Movement) and extension (like .csv)
    file_name_without_extension, file_extension = os.path.splitext(file_name)

    # Fetch measurement option ID
    get_measurement_id = """
    SELECT m.measurement_option_id
    FROM measurement_option AS m
    WHERE m.measurement_option_name = %s
    """
    cur.execute(get_measurement_id, (file_name_without_extension,))
    result = cur.fetchone()
    if not result:
        raise ValueError(
            f"No measurement option found for '{file_name_without_extension}'"
        )

    measurement_option_id = result[0]

    # Insert session data instance
    insert_session_data_instance = """
    INSERT INTO session_data_instance (trial_id, measurement_option_id)
    VALUES(%s, %s)
    """
    cur.execute(insert_session_data_instance, (trial_id, measurement_option_id))
    conn.commit()

    # Get the inserted session data instance ID
    cur.execute("SELECT LAST_INSERT_ID()")
    session_data_instance_id = cur.fetchone()[0]

    # Create the new absolute path for the file in the participant's trial folder
    absolute_data_instance_path = os.path.join(
        participant_dir,
        f"{session_data_instance_id}{file_extension}",
    )

    # Update the results path in the database
    update_results_path = """
    UPDATE session_data_instance
    SET results_path = %s
    WHERE session_data_instance_id = %s
    """
    cur.execute(
        update_results_path, (absolute_data_instance_path, session_data_instance_id)
    )
    conn.commit()

    # Use shutil.move instead of os.rename: /tmp is overlayfs but
    # RESULTS_BASE_DIR_PATH is a named volume, so os.rename raises EXDEV.
    shutil.move(data_instance_path, absolute_data_instance_path)


def get_zip(results_with_size, study_id, conn, mode):

    # Fetch the required data for folder naming
    participant_sessions = get_participant_session_name_for_folder(
        study_id, conn.cursor()
    )
    cur = conn.cursor()

    # Create an in-memory ZIP file
    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zipf:

        # Iterate over the session data results and organize files in the ZIP
        for (
            study_name,
            session_data_instance_id,
            results_path,
            trial_id,
            task_id,
            task_name,
            measurement_option_id,
            measurement_option_name,
            factor_id,
            factor_name,
            participant_session_id,
        ) in results_with_size:

            participant_session_name = participant_sessions.get(
                participant_session_id, "UnknownSession"
            )
            trial_order = get_trial_order_for_folder(
                participant_session_id, conn.cursor()
            ).get(trial_id, "UnknownTrialOrdering")

            if mode == "study" or mode == "participant":
                trial_folder = f"{task_name}_{factor_name}_trial_{trial_order}"
                participant_session_folder = (
                    f"{participant_session_name}_participant_session/{trial_folder}"
                )

                # Extract the file extension
                file_extension = os.path.splitext(results_path)[1]
                zip_file_path = f"{participant_session_folder}/{measurement_option_name}{file_extension}"
            elif mode == "participant_session":
                trial_folder = f"{task_name}_{factor_name}_trial_{trial_order}"

                # Extract the file extension
                file_extension = os.path.splitext(results_path)[1]
                zip_file_path = (
                    f"{trial_folder}/{measurement_option_name}{file_extension}"
                )
            elif mode == "one file" or mode == "trial":
                # Extract the file extension
                file_extension = os.path.splitext(results_path)[1]
                zip_file_path = f"{measurement_option_name}{file_extension}"

            try:
                with open(results_path, "rb") as file:
                    zipf.writestr(zip_file_path, file.read())
                    logger.info(f"Successfully added file to ZIP: {results_path}")
            except (IOError, PermissionError) as e:
                logger.warning(f"Cannot access file: {results_path} - Error: {str(e)}")
                # If file type is CSV, create a placeholder with headers
                if results_path.endswith(".csv"):
                    # Create an empty CSV with basic headers for this data type
                    placeholder_content = "timestamp,running_time,x,y\n0,0,0,0\n"
                    zipf.writestr(zip_file_path, placeholder_content)
                    logger.warning(
                        f"Added placeholder CSV for inaccessible file: {results_path}"
                    )
                # If file type is PNG, create a tiny image
                elif results_path.endswith(".png"):
                    # We can't create a useful image, so just log and continue
                    logger.warning(f"Skipping inaccessible PNG file: {results_path}")
                # If file type is MP4, just skip
                elif results_path.endswith(".mp4"):
                    logger.warning(f"Skipping inaccessible MP4 file: {results_path}")
                else:
                    logger.warning(f"Skipping unknown file type: {results_path}")

        # Are we looking at the study-level (many sessions) or looking at a single session
        if mode == "participant_session":
            participant_session_ids = {row[-1] for row in results_with_size}
            participant_sessions_filtered = {
                pid: participant_sessions.get(pid, "UnknownSession")
                for pid in participant_session_ids
            }
        else:
            participant_sessions_filtered = participant_sessions

        # Grab pre/post survey responses
        for (
            participant_session_id,
            participant_number,
        ) in participant_sessions_filtered.items():
            survey_query = """
                SELECT
                    survey_results.file_path,
                    survey_form.form_type
                FROM survey_results
                INNER JOIN survey_form
                ON survey_results.survey_form_id = survey_form.survey_form_id
                WHERE survey_results.participant_session_id = %s
            """
            cur.execute(survey_query, (participant_session_id,))
            survey_results = cur.fetchall()

            for file_path, form_type in survey_results:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)

                    if mode == "participant_session":
                        survey_folder = f"{form_type}_survey"
                    else:
                        folder = f"{participant_number}_participant_session"
                        survey_folder = f"{folder}/{form_type}_survey"
                    zip_path = f"{survey_folder}/{filename}"

                    with open(file_path, "rb") as f:
                        zipf.writestr(zip_path, f.read())

    memory_file.seek(0)
    return memory_file


def get_core_csv_files_query():
    return """
SELECT 
    s.study_name,
    sdi.session_data_instance_id,
    sdi.results_path,
    tr.trial_id,
    tr.task_id,
    t.task_name,
    sdi.measurement_option_id,
    mo.measurement_option_name,
    tr.factor_id,
    f.factor_name,
    ps.participant_session_id
FROM session_data_instance sdi
INNER JOIN trial tr
    ON tr.trial_id = sdi.trial_id
INNER JOIN participant_session ps
    ON ps.participant_session_id = tr.participant_session_id
INNER JOIN task AS t
    ON t.study_id = ps.study_id AND t.task_id = tr.task_id
INNER JOIN factor AS f
    ON f.study_id = ps.study_id AND f.factor_id = tr.factor_id
INNER JOIN study AS s
    ON s.study_id = f.study_id
INNER JOIN measurement_option AS mo
    ON mo.measurement_option_id = sdi.measurement_option_id
    """


def get_trial_order_for_folder(participant_session_id, cur):
    query = """
    SELECT t.trial_id, t.started_at
    FROM trial AS t
    WHERE participant_session_id = %s
    ORDER BY t.started_at DESC
    """
    cur.execute(query, (participant_session_id,))
    results = cur.fetchall()

    trial_order = {}
    counter = 1
    for result in results:
        trial_order[result[0]] = counter
        counter += 1
    return trial_order


def get_participant_session_name_for_folder(study_id, cur):
    query = """
    SELECT ps.participant_session_id, ps.created_at
    FROM participant_session AS ps
    WHERE study_id = %s
    ORDER BY ps.created_at ASC
    """
    cur.execute(query, (study_id,))
    results = cur.fetchall()

    participant_sessions = {}
    counter = 1
    for result in results:
        participant_sessions[result[0]] = counter
        counter += 1
    return participant_sessions


def get_participant_name_for_folder(study_id, cur):
    query = """
    SELECT ps.participant_id, p.created_at
    FROM participant_session AS ps
    INNER JOIN participant AS p
    ON p.participant_id = ps.participant_id
    WHERE study_id = %s
    ORDER BY ps.created_at ASC
    """
    cur.execute(query, (study_id,))
    results = cur.fetchall()

    participant_sessions = {}
    counter = 1
    for result in results:
        participant_sessions[result[0]] = counter
        counter += 1
    return participant_sessions


def get_file_name_for_folder(study_id, cur):
    query = """
    SELECT sdi.session_data_instance_id, mo.measurement_option_name
    FROM session_data_instance AS sdi
    INNER JOIN measurement_option AS mo
    ON mo.measurement_option_id = sdi.measurement_option_id
    INNER JOIN trial AS t
    ON t.trial_id = sdi.trial_id
    INNER JOIN participant_session AS ps
    ON ps.participant_session_id = t.participant_session_id
    WHERE ps.study_id = %s
    """
    cur.execute(query, (study_id,))
    results = cur.fetchall()
    file_names = {}

    for result in results:
        file_names[result[0]] = result[1]
    return file_names


def get_all_participant_csv_files(participant_id, cur):
    query = get_core_csv_files_query() + "WHERE ps.participant_id = %s"
    cur.execute(query, (participant_id,))
    results = cur.fetchall()
    return results


def get_all_participant_session_csv_files(participant_session_id, cur):
    query = get_core_csv_files_query() + "WHERE ps.participant_session_id = %s"
    cur.execute(query, (participant_session_id,))
    results = cur.fetchall()
    return results


def get_one_csv_file(session_data_instance_id, cur):
    query = get_core_csv_files_query() + "WHERE sdi.session_data_instance_id = %s"
    cur.execute(query, (session_data_instance_id,))
    results = cur.fetchall()
    return results


def get_all_study_csv_files(study_id, cur):
    query = (
        get_core_csv_files_query()
        + "WHERE ps.study_id = %s ORDER BY sdi.session_data_instance_id"
    )

    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Executing query to get study files: {query}")
    logger.info(f"Study ID parameter: {study_id}")

    cur.execute(query, (study_id,))
    results = cur.fetchall()

    logger.info(f"Found {len(results)} files for study {study_id}")

    # Validate result paths
    import os

    missing_files = 0
    for result in results:
        file_path = result[2]  # results_path is at index 2
        if not os.path.exists(file_path):
            missing_files += 1
            logger.warning(f"File does not exist: {file_path}")

    logger.info(f"Found {missing_files} missing files out of {len(results)}")
    return results


def get_one_trial(trial_id, cur):
    query = get_core_csv_files_query() + "WHERE tr.trial_id = %s"
    cur.execute(query, (trial_id,))
    results = cur.fetchall()
    return results
