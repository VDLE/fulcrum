import base64
import pandas as pd
import os
import shutil
from app.utility.db_connection import get_db_connection
from flask import current_app
from werkzeug.utils import secure_filename


def set_available_features(task_measurments):
    # makes sures the default taks are false
    default_tasks = {
        "Mouse Movement": False,
        "Mouse Scrolls": False,
        "Mouse Clicks": False,
        "Keyboard Inputs": False,
    }

    # checks if features are in the array, then it will change hash into true
    for task in task_measurments:
        if task in default_tasks:
            default_tasks[task] = True

    return default_tasks


# 0 no access, 1 is owner, 2 is editor, 3 is viewer
def check_user_study_access(cur, study_id, user_id):
    try:
        # Check if user has access
        check_user_query = """
        SELECT study_user_role_description 
        FROM study_user_role sur
        INNER JOIN study_user_role_type surt
        ON surt.study_user_role_type_id = sur.study_user_role_type_id
        WHERE user_id = %s AND study_id = %s
        """
        cur.execute(
            check_user_query,
            (
                user_id,
                study_id,
            ),
        )
        user_access_exists = cur.fetchone()

        if user_access_exists is None:
            return 0
        elif user_access_exists[0] == "Owner":
            return 1
        elif user_access_exists[0] == "Editor":
            return 2
        elif user_access_exists[0] == "Viewer":
            return 3

    except Exception as e:
        # Raise the error to be handled by the calling function
        raise Exception(f"Error creating study: {str(e)}")


def create_study_data(study_data, user_id, cur):
    try:
        # Insert study details
        study_id = create_study_details(study_data, cur)
        create_study_task_factor_details(study_id, study_data, cur)

        # Get owner role ID
        cur.execute(
            """
            SELECT study_user_role_type_id 
            FROM study_user_role_type 
            WHERE study_user_role_description = 'Owner'
            """
        )
        study_user_role_type_id = cur.fetchone()[0]

        # Assign owner role
        cur.execute(
            """
            INSERT INTO study_user_role (user_id, study_id, study_user_role_type_id)
            VALUES (%s, %s, %s)
            """,
            (user_id, study_id, study_user_role_type_id),
        )

        # Save base64-encoded consent file if present
        if "consentFile" in study_data:
            file_info = study_data["consentFile"]
            filename = secure_filename(file_info.get("filename"))
            base64_data = file_info.get("content")

            if filename and base64_data:
                file_bytes = base64.b64decode(base64_data)
                base_dir = current_app.config.get("RESULTS_BASE_DIR_PATH")
                full_path = os.path.join(base_dir, "study_consent_forms", str(study_id))

                os.makedirs(full_path, exist_ok=True)
                with open(os.path.join(full_path, filename), "wb") as f:
                    f.write(file_bytes)

        return study_id
    except Exception as e:
        # Raise the error to be handled by the calling function
        raise Exception(f"Error creating study: {str(e)}")


def get_all_study_data_helper(study_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get Study Details
        get_study_info = """
        SELECT
            s.study_name AS 'User Study Name',
            s.study_description AS 'Description',
            s.expected_participants AS '# Expected Participants',
            surt.study_user_role_description AS 'Role',
            sdt.study_design_type_description AS 'Study Design Type'
        FROM study AS s
        INNER JOIN study_user_role AS sur
            ON sur.study_id = s.study_id
        INNER JOIN study_user_role_type AS surt
            ON sur.study_user_role_type_id = surt.study_user_role_type_id
        INNER JOIN study_design_type AS sdt
            ON s.study_design_type_id = sdt.study_design_type_id
        WHERE s.study_id = %s
        """
        cur.execute(get_study_info, (study_id,))
        study_res = cur.fetchone()

        # Get all the tasks under the study
        get_tasks = """
        SELECT
            task_id AS 'Task ID',
            task_name AS 'Task Name',
            task_description AS 'Task Description',
            task_directions AS 'Task Directions',
            duration AS 'Duration'
        FROM task
        WHERE study_id = %s;
        """
        cur.execute(get_tasks, (study_id,))
        task_res = cur.fetchall()

        # Get all the factors under the study
        get_factors = """
        SELECT
            factor_id AS 'Factor ID',
            factor_name AS 'Factor Name',
            factor_description AS 'Factor Description'
        FROM factor
        WHERE study_id = %s;
        
        """
        cur.execute(get_factors, (study_id,))
        factor_res = cur.fetchall()

        # Creating the study obj before adding measurement option info
        study_data = {
            "studyName": study_res[0],
            "studyDescription": study_res[1],
            "studyDesignType": study_res[4],
            "participantCount": str(study_res[2]),
            "tasks": [
                {
                    "taskID": task[0],
                    "taskName": task[1],
                    "taskDescription": task[2],
                    "taskDirections": task[3],
                    "taskDuration": task[4],
                    "measurementOptions": [],
                }
                for task in task_res
            ],
            "factors": [
                {
                    "factorID": factor[0],
                    "factorName": factor[1],
                    "factorDescription": factor[2],
                }
                for factor in factor_res
            ],
        }

        # Get all the measurements under the task under the study
        get_task_measurements = """
        SELECT
            tm.task_id AS 'Task ID',
            mo.measurement_option_name AS 'Measurement Option'
        FROM task_measurement AS tm
        JOIN task AS t
        ON tm.task_id = t.task_id
        JOIN measurement_option AS mo
        ON tm.measurement_option_id = mo.measurement_option_id
        WHERE tm.task_id IN (SELECT task_id FROM task WHERE study_id = %s);
        """
        cur.execute(get_task_measurements, (study_id,))
        measurement_res = cur.fetchall()

        # Use taskID to get the measurement types into the correct task measurement[]
        for task in study_data["tasks"]:
            task["measurementOptions"] = [
                measurement[1]
                for measurement in measurement_res
                if measurement[0] == task["taskID"]
            ]

        cur.close()

        return study_data

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        raise Exception(f"Error retrieving study data: {error_message}")


def get_study_detail(subData):
    study_name = subData.get("studyName")
    study_desc = subData.get("studyDescription")
    study_design = subData.get("studyDesignType")
    people_count = subData.get("participantCount")

    return (
        study_name,
        study_desc,
        study_design,
    )


def create_study_details(submissionData, cur):
    try:
        # Get study_design_type
        cur.execute(
            "SELECT study_design_type_id FROM study_design_type WHERE study_design_type_description = %s",
            (submissionData["studyDesignType"],),
        )
        result = cur.fetchone()
        study_design_type_id = result[0]

        # Insert study
        insert_study_query = """
        INSERT INTO study (study_name, study_description, study_design_type_id, expected_participants)
        VALUES (%s, %s, %s, %s)
        """
        study_name = submissionData["studyName"]
        study_description = submissionData["studyDescription"]
        expected_participants = submissionData["participantCount"]

        # Execute study insert
        cur.execute(
            insert_study_query,
            (
                study_name,
                study_description,
                study_design_type_id,
                expected_participants,
            ),
        )

        return cur.lastrowid
    except Exception as e:
        raise Exception(f"Error creating study: {str(e)}")


def create_study_task_factor_details(study_id, submissionData, cur):
    try:
        # Insert tasks
        insert_task_query = """
        INSERT INTO task (task_name, study_id, task_description, task_directions, duration)
        VALUES (%s, %s, %s, %s, %s)
        """
        for task in submissionData["tasks"]:
            task_name = task["taskName"]
            task_description = task["taskDescription"]
            task_directions = task["taskDirections"]
            task_duration = task.get("taskDuration", None)

            # Error handling for bad duration inputs. Convert empty or invalid values to None
            if task_duration is not None:
                try:
                    task_duration = float(task_duration) if task_duration else None
                except ValueError:
                    task_duration = None

            # Execute insert for each task
            cur.execute(
                insert_task_query,
                (task_name, study_id, task_description, task_directions, task_duration),
            )

            # Get the task_id of the newly inserted task
            task_id = cur.lastrowid

            # Define query for getting measurement_option_id
            select_measurement_option_query = """
            SELECT measurement_option_id FROM measurement_option WHERE measurement_option_name = %s
            """
            # Define query for inserting task_measurement
            insert_measurement_query = """
            INSERT INTO task_measurement (task_id, measurement_option_id)
            VALUES (%s, %s)
            """
            # Process each measurement option for the task
            for measurement_option in task["measurementOptions"]:
                # Get id for each measurement option
                cur.execute(select_measurement_option_query, (measurement_option,))
                result = cur.fetchone()
                if result:
                    measurement_option_id = result[0]

                    # Insert task-to-measurement
                    cur.execute(
                        insert_measurement_query, (task_id, measurement_option_id)
                    )

        # Insert factors
        for factor in submissionData["factors"]:
            insert_factor_query = """
            INSERT INTO factor (study_id, factor_name, factor_description)
            VALUES (%s, %s, %s)
            """
            factor_name = factor["factorName"]
            factor_description = factor["factorDescription"]
            cur.execute(
                insert_factor_query,
                (
                    study_id,
                    factor_name,
                    factor_description,
                ),
            )
    except Exception as e:
        raise Exception(f"Error creating study: {str(e)}")


# Stores consent form in the study-level dir in the filesystem
def save_study_consent_form(study_id, file, cur, base_dir):
    original_filename = secure_filename(file.get("filename"))

    # Check if the file is a PDF
    if not original_filename.lower().endswith(".pdf"):
        raise ValueError("Invalid file type. Only PDF files are allowed.")

    # Decode base64 content
    content = file.get("content")
    if not content:
        raise ValueError("Missing file content.")

    # Construct path
    full_path = os.path.join(base_dir, f"{study_id}_study_id")
    os.makedirs(full_path, exist_ok=True)

    file_path = os.path.join(full_path, "consent_form.pdf")

    # Save decoded bytes to file
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(content))

    # Insert or update the consent form in the database
    insert_consent_form = """
    INSERT INTO consent_form(study_id, file_path, original_filename)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE
        file_path = VALUES(file_path),
        original_filename = VALUES(original_filename),
        uploaded_at = CURRENT_TIMESTAMP;
    """
    cur.execute(insert_consent_form, (study_id, file_path, original_filename))


# Removing consent form
def remove_study_consent_form(study_id, cur):
    # Get file path if one exists
    look_path = """
    SELECT file_path
    FROM consent_form
    WHERE study_id = %s
    """
    cur.execute(look_path, (study_id,))
    result = cur.fetchone()

    if not result:
        return

    file_path = result[0]

    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except Exception as err:
            print(f"Failed removing file at {file_path}: {err}")

    # Updating consent form tbl to reflect deletion
    delete_consent_tbl_entry = """
    DELETE
    FROM consent_form
    WHERE study_id = %s
    """
    cur.execute(delete_consent_tbl_entry, (study_id,))


# Stores survey forms in the study-level dir in the filesystem
def save_study_survey_form(study_id, file, cur, base_dir, survey_type):
    original_filename = secure_filename(file.get("filename"))

    # Check if the file is a JSON
    if not original_filename.lower().endswith(".json"):
        raise ValueError("Invalid survey file type. JSON file needed.")

    # Decode base64 content
    content = file.get("content")
    if not content:
        raise ValueError("Missing survey file content.")

    # Construct path
    full_path = os.path.join(base_dir, f"{study_id}_study_id")
    os.makedirs(full_path, exist_ok=True)

    survey_name = None
    if survey_type not in ["pre", "post"]:
        raise ValueError("Invalid survey type received.")
    survey_name = f"{survey_type}_survey_form.json"

    file_path = os.path.join(full_path, survey_name)

    # Save decoded bytes to file
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(content))

    # Insert or update the survey form in the database
    insert_survey_form = """
    INSERT INTO survey_form(study_id, form_type, file_path, original_filename)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        file_path = VALUES(file_path),
        original_filename = VALUES(original_filename),
        uploaded_at = CURRENT_TIMESTAMP;
    """
    cur.execute(
        insert_survey_form, (study_id, survey_type, file_path, original_filename)
    )


# Remove survey forms
def remove_study_survey_form(study_id, cur, survey_type):
    if survey_type not in ["pre", "post"]:
        raise ValueError("Invalid survey type received.")

    # Get file path if one exists
    look_path = """
    SELECT file_path
    FROM survey_form
    WHERE study_id = %s AND form_type = %s
    """
    cur.execute(look_path, (study_id, survey_type))
    result = cur.fetchone()

    if not result:
        return

    file_path = result[0]

    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except Exception as err:
            print(f"Failed removing file at {file_path}: {err}")

    # Updating survey form tbl to reflect deletion
    delete_survey_tbl_entry = """
    DELETE
    FROM survey_form
    WHERE study_id = %s AND form_type = %s
    """
    cur.execute(delete_survey_tbl_entry, (study_id, survey_type))


# Duplicating consent form (if it exists)
def copy_consent_form(old_study_id, new_study_id, cur, base_dir):
    # Get file path if one exists
    look_file_to_duplicate = """
    SELECT file_path, original_filename
    FROM consent_form
    WHERE study_id = %s
    """
    cur.execute(look_file_to_duplicate, (old_study_id,))
    result = cur.fetchone()

    if not result:
        return "skipped"  # No consent form for this study to duplicate

    src_file_path, original_filename = result

    if not (src_file_path and os.path.isfile(src_file_path)):
        return "failure"  # File supposed to exist according to db but failed to find it in filesystem

    try:
        dst_dir = os.path.join(base_dir, f"{new_study_id}_study_id")
        os.makedirs(dst_dir, exist_ok=True)

        dst_file_path = os.path.join(dst_dir, "consent_form.pdf")
        shutil.copy2(src_file_path, dst_file_path)

        # Insert or update the consent form in the database
        insert_consent_form = """
        INSERT INTO consent_form(study_id, file_path, original_filename)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            file_path = VALUES(file_path),
            original_filename = VALUES(original_filename),
            uploaded_at = CURRENT_TIMESTAMP;
        """
        cur.execute(
            insert_consent_form, (new_study_id, dst_file_path, original_filename)
        )

        return "success"

    except Exception as err:
        print(f"Failed duplicate file at {src_file_path} into {dst_file_path}: {err}")
        return "failure"


# Duplicating survey form (if it exists)
def copy_survey_form(old_study_id, new_study_id, cur, base_dir, survey_type):
    # Get file path if one exists
    look_file_to_duplicate = """
    SELECT file_path, original_filename
    FROM survey_form
    WHERE study_id = %s AND form_type = %s
    """
    cur.execute(look_file_to_duplicate, (old_study_id, survey_type))
    result = cur.fetchone()

    if not result:
        return "skipped"  # No survey form for this study to duplicate

    src_file_path, original_filename = result

    if not (src_file_path and os.path.isfile(src_file_path)):
        return "failure"  # File supposed to exist according to db but failed to find it in filesystem

    try:
        dst_dir = os.path.join(base_dir, f"{new_study_id}_study_id")
        os.makedirs(dst_dir, exist_ok=True)

        dst_file_path = os.path.join(dst_dir, f"{survey_type}_survey_form.json")
        shutil.copy2(src_file_path, dst_file_path)

        # Insert or update the survey form in the database
        insert_survey_form = """
        INSERT INTO survey_form(study_id, form_type, file_path, original_filename)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            file_path = VALUES(file_path),
            original_filename = VALUES(original_filename),
            uploaded_at = CURRENT_TIMESTAMP;
        """
        cur.execute(
            insert_survey_form,
            (new_study_id, survey_type, dst_file_path, original_filename),
        )

        return "success"

    except Exception as err:
        print(
            f"Failed duplicate {survey_type} survey file at {src_file_path} into {dst_file_path}: {err}"
        )
        return "failure"
