import base64
from io import BytesIO
import os

import requests
from flask import Blueprint, current_app, request, jsonify, Response, send_file
import json
from jsonschema import validate, ValidationError
import pandas as pd
from app.utility.studies import (
    check_user_study_access,
    create_study_data,
    create_study_details,
    create_study_task_factor_details,
    save_study_consent_form,
    remove_study_consent_form,
    get_all_study_data_helper,
    save_study_survey_form,
    remove_study_survey_form,
    copy_consent_form,
    copy_survey_form,
)
from app.utility.db_connection import get_db_connection
from flask_security import auth_required
from flask_login import current_user


bp = Blueprint("studies", __name__)


# Gets and saves data from study form page and stores it into a json file. Then uploads data into db
@bp.route("/api/create_study", methods=["POST"])
@auth_required()
def create_study():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Get JSON data from the request body
        submission_data = request.get_json()

        if not submission_data:
            return jsonify({"error": "Missing JSON body"}), 400

        study_id = create_study_data(submission_data, current_user.id, cur)

        # Handle files (optional)
        base_dir = current_app.config.get("RESULTS_BASE_DIR_PATH")
        if "consentFile" in submission_data:
            file = submission_data["consentFile"]
            save_study_consent_form(study_id, file, cur, base_dir)
        if "preSurveyFile" in submission_data:
            pre_file = submission_data["preSurveyFile"]
            save_study_survey_form(study_id, pre_file, cur, base_dir, "pre")
        if "postSurveyFile" in submission_data:
            post_file = submission_data["postSurveyFile"]
            save_study_survey_form(study_id, post_file, cur, base_dir, "post")

        conn.commit()
        return (
            jsonify({"message": "Study created successfully", "study_id": study_id}),
            200,
        )

    except Exception as e:
        if "conn" in locals():
            conn.rollback()

        error_type = type(e).__name__
        error_message = str(e)
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


@bp.route("/api/get_all_user_access_for_study", methods=["POST"])
@auth_required()
def get_all_user_access_for_study():
    # Get JSON data
    submission_data = request.get_json()

    if not submission_data or "studyID" not in submission_data:
        return jsonify({"error": "Missing studyID in request body"}), 400

    study_id = submission_data["studyID"]
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        user_access_type = check_user_study_access(cur, study_id, current_user.id)

        # No access
        if user_access_type == 0:
            return jsonify({"message": "User lacks access"}), 403

        get_all_access = """
        SELECT us.email, study_user_role_description AS role
        FROM study_user_role as sur
        INNER JOIN user AS us
        ON us.user_id = sur.user_id
        INNER JOIN study_user_role_type AS surt
        ON surt.study_user_role_type_id = sur.study_user_role_type_id
        WHERE sur.study_id = %s
        """

        cur.execute(get_all_access, (study_id,))

        get_all_access_results = cur.fetchall()

        access_map = {1: "Owner", 2: "Editor", 3: "Viewer"}

        get_study_name = """
        SELECT study_name
        FROM study
        WHERE study_id = %s
        """
        cur.execute(get_study_name, (study_id,))
        study_name = cur.fetchone()[0]

        get_requesting_user_email = """
        SELECT email
        FROM user
        WHERE user_id = %s
        """
        cur.execute(get_requesting_user_email, (current_user.id,))
        requesting_user_email = cur.fetchone()[0]
        return (
            jsonify(
                {
                    "requesting user's role": access_map.get(
                        user_access_type, "Unknown access level"
                    ),
                    "requesting user's email": requesting_user_email,
                    "data": get_all_access_results,
                    "study_name": study_name,
                }
            ),
            200,
        )

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


# Editor / Viewer leave
@bp.route("/api/leave_user_study_access", methods=["POST"])
@auth_required()
def leave_user_study_access():
    # Get JSON data
    submission_data = request.get_json()

    if (
        not submission_data
        or "studyID" not in submission_data
        or "desiredUserEmail" not in submission_data
    ):
        return jsonify({"error": "Missing needed info for request body"}), 400

    study_id = submission_data["studyID"]
    removed_user_email = submission_data["desiredUserEmail"]
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        user_access_type = check_user_study_access(cur, study_id, current_user.id)

        # Editor / Viewer
        if user_access_type == 2 or user_access_type == 3:
            get_user_id = """
            SELECT user_id
            FROM user
            WHERE email = %s
            """
            cur.execute(get_user_id, (removed_user_email,))
            result = cur.fetchone()[0]

            delete_user_access = """
            DELETE FROM study_user_role
            WHERE study_id = %s AND user_id = %s
            """
            cur.execute(
                delete_user_access,
                (
                    study_id,
                    result,
                ),
            )
            conn.commit()
            return jsonify({"message": "User access removed successfully"}), 200
        else:
            return jsonify({"message": "User lacks editor or viewer access"}), 403

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


# Owner remove
@bp.route("/api/remove_user_study_access", methods=["POST"])
@auth_required()
def remove_user_study_access():
    # Get JSON data
    submission_data = request.get_json()

    if (
        not submission_data
        or "studyID" not in submission_data
        or "desiredUserEmail" not in submission_data
    ):
        return jsonify({"error": "Missing needed info for request body"}), 400

    study_id = submission_data["studyID"]
    removed_user_email = submission_data["desiredUserEmail"]
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        user_access_type = check_user_study_access(cur, study_id, current_user.id)

        # Owner
        if user_access_type == 1:
            get_user_id = """
            SELECT user_id
            FROM user
            WHERE email = %s
            """
            cur.execute(get_user_id, (removed_user_email,))
            result = cur.fetchone()[0]

            delete_user_access = """
            DELETE FROM study_user_role
            WHERE study_id = %s AND user_id = %s
            """
            cur.execute(
                delete_user_access,
                (
                    study_id,
                    result,
                ),
            )
            conn.commit()
            return jsonify({"message": "User access removed successfully"}), 200
        # Not Owner
        else:
            return jsonify({"message": "User lacks owner access"}), 403

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


@bp.route("/api/change_user_access_type", methods=["POST"])
@auth_required()
def change_user_access_type():
    # Get JSON data
    submission_data = request.get_json()

    if (
        not submission_data
        or "studyID" not in submission_data
        or "desiredUserEmail" not in submission_data
        or "roleType" not in submission_data
    ):
        return jsonify({"error": "Missing needed info for request body"}), 400

    study_id = submission_data["studyID"]
    edit_user_email = submission_data["desiredUserEmail"]
    role_type = submission_data["roleType"]
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        user_access_type = check_user_study_access(cur, study_id, current_user.id)

        # Not Owner
        if user_access_type != 1 and user_access_type != 2:
            return jsonify({"message": "User lacks owner / editor access"}), 403

        get_user_id = """
        SELECT user_id
        FROM user
        WHERE email = %s
        """
        cur.execute(get_user_id, (edit_user_email,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "User not found"}), 404
        user_id_result = row[0]
        print(user_id_result)
        # Check requested user's access type
        edit_user_current_access = check_user_study_access(
            cur, study_id, user_id_result
        )

        if edit_user_current_access == 0:
            return (
                jsonify(
                    {
                        "message": "Cannot edit access for a user that lacks access. Create access first"
                    }
                ),
                409,
            )
        elif edit_user_current_access == 1:
            return (
                jsonify({"error": "Cannot edit access for the owner"}),
                409,
            )

        access_type_id = """
        SELECT surt.study_user_role_type_id
        FROM study_user_role_type AS surt
        WHERE surt.study_user_role_description = %s
        """

        cur.execute(access_type_id, (role_type,))

        role_type_result = cur.fetchone()

        if role_type_result is None:
            return jsonify({"error": "Internal server error getting role type"}), 500

        edit_user_access = """
        UPDATE study_user_role
        SET study_user_role_type_id = %s
        WHERE study_id = %s AND user_id = %s
        """
        cur.execute(edit_user_access, (role_type_result[0], study_id, user_id_result))
        conn.commit()
        return jsonify({"message": "User access edited successfully"}), 200

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


@bp.route("/api/add_user_study_access", methods=["POST"])
@auth_required()
def add_user_study_access():
    # Get JSON data
    submission_data = request.get_json()

    if (
        not submission_data
        or "studyID" not in submission_data
        or "desiredUserEmail" not in submission_data
        or "roleType" not in submission_data
    ):
        return jsonify({"error": "Missing needed info for request body"}), 400

    study_id = submission_data["studyID"]
    add_user_email = submission_data["desiredUserEmail"]
    role_type = submission_data["roleType"]
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        user_access_type = check_user_study_access(cur, study_id, current_user.id)

        # Not Owner
        if user_access_type != 1 and user_access_type != 2:
            return jsonify({"message": "User cannot add others"}), 403

        get_user_id = """
        SELECT user_id
        FROM user
        WHERE email = %s
        """
        cur.execute(get_user_id, (add_user_email,))
        user_id_result = cur.fetchone()[0]

        # Check if access already exists
        add_user_current_access = check_user_study_access(cur, study_id, user_id_result)

        if add_user_current_access != 0:
            return jsonify({"message": "Requested user already has access"}), 409

        access_type_id = """
        SELECT surt.study_user_role_type_id
        FROM study_user_role_type AS surt
        WHERE surt.study_user_role_description = %s
        """

        cur.execute(access_type_id, (role_type,))

        role_type_result = cur.fetchone()

        if role_type_result is None:
            return jsonify({"error": "Internal server error getting role type"}), 500

        add_user_access = """
        INSERT INTO study_user_role (study_id, user_id, study_user_role_type_id)
        VALUES (%s, %s, %s)
        """
        cur.execute(
            add_user_access,
            (study_id, user_id_result, role_type_result[0]),
        )
        conn.commit()
        return jsonify({"message": "User access added successfully"}), 200

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


@bp.route("/api/is_overwrite_study_allowed", methods=["POST"])
@auth_required()
def is_overwrite_study_allowed():
    # Get JSON data
    submission_data = request.get_json()

    if not submission_data or "studyID" not in submission_data:
        return jsonify({"error": "Missing studyID in request body"}), 400

    study_id = submission_data["studyID"]
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        user_access_type = check_user_study_access(cur, study_id, current_user.id)

        # No access / Viewer
        if user_access_type == 0 or user_access_type == 3:
            return jsonify(False), 200
        # Owner / Editor
        elif user_access_type == 1 or user_access_type == 2:
            # If sessions exist, info can't be overwritten
            check_sessions_query = """
            SELECT participant_session_id
            FROM participant_session
            WHERE study_id = %s 
            """
            cur.execute(check_sessions_query, (study_id,))
            sessions_exist = cur.fetchone()

            # Error Message
            if sessions_exist is not None:
                return (
                    jsonify(False),
                    200,
                )
            else:
                return (
                    jsonify(True),
                    200,
                )

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


@bp.route("/api/overwrite_study", methods=["POST"])
@auth_required()
def overwrite_study():
    submission_data = request.get_json()

    if not submission_data:
        return jsonify({"error": "No study data provided"}), 400

    study_id = submission_data.get("studyID")
    if not study_id:
        return jsonify({"error": "Missing studyID in submission"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if study exists
        cur.execute("SELECT study_id FROM study WHERE study_id = %s", (study_id,))
        if cur.fetchone() is None:
            return jsonify({"error": "Study does not exist"}), 404

        # Check user role
        cur.execute(
            """
            SELECT study_user_role_description 
            FROM study_user_role sur
            INNER JOIN study_user_role_type surt
            ON surt.study_user_role_type_id = sur.study_user_role_type_id
            WHERE user_id = %s AND study_id = %s
        """,
            (current_user.id, study_id),
        )
        role_result = cur.fetchone()

        if role_result is None:
            return jsonify({"error": "User does not have access to study"}), 403
        if role_result[0] == "Viewer":
            return jsonify({"error": "User may only view this study"}), 403

        # Check if sessions exist
        cur.execute(
            "SELECT participant_session_id FROM participant_session WHERE study_id = %s",
            (study_id,),
        )
        if cur.fetchone():
            return (
                jsonify(
                    {
                        "error": "Sessions already exist, so the study may not be overwritten"
                    }
                ),
                400,
            )

        # Delete existing tasks/factors
        cur.execute("DELETE FROM task WHERE study_id = %s", (study_id,))
        cur.execute("DELETE FROM factor WHERE study_id = %s", (study_id,))

        # Resolve study_design_type_id
        cur.execute(
            "SELECT study_design_type_id FROM study_design_type WHERE study_design_type_description = %s",
            (submission_data["studyDesignType"],),
        )
        study_design_type_id = cur.fetchone()[0]

        # Update study core info
        cur.execute(
            """
            UPDATE study 
            SET study_name = %s,
                study_description = %s,
                study_design_type_id = %s,
                expected_participants = %s
            WHERE study_id = %s
        """,
            (
                submission_data["studyName"],
                submission_data["studyDescription"],
                study_design_type_id,
                submission_data["participantCount"],
                study_id,
            ),
        )

        # Recreate task/factor entries
        create_study_task_factor_details(study_id, submission_data, cur)

        base_dir = current_app.config.get("RESULTS_BASE_DIR_PATH")
        # Handle consent file (optional)
        if "consentFile" in submission_data:
            file = submission_data["consentFile"]
            save_study_consent_form(study_id, file, cur, base_dir)
        else:
            # No file present → remove existing file
            remove_study_consent_form(study_id, cur)

        # Handle pre survey file (optional)
        if "preSurveyFile" in submission_data:
            pre_file = submission_data["preSurveyFile"]
            save_study_survey_form(study_id, pre_file, cur, base_dir, "pre")
        else:
            # Attempt to remove existing file
            remove_study_survey_form(study_id, cur, "pre")

        # Handle post survey file (optional)
        if "postSurveyFile" in submission_data:
            post_file = submission_data["postSurveyFile"]
            save_study_survey_form(study_id, post_file, cur, base_dir, "post")
        else:
            # Attempt to remove existing file
            remove_study_survey_form(study_id, cur, "post")

        conn.commit()
        cur.close()
        return jsonify({"message": "Study overwritten successfully"}), 200

    except Exception as e:
        if "conn" in locals():
            conn.rollback()
        return jsonify({"error_type": type(e).__name__, "error_message": str(e)}), 500


@bp.route("/api/get_study_data", methods=["GET"])
@auth_required()
def get_study_data():
    # https://www.geeksforgeeks.org/read-json-file-using-python/
    # gets the json data from the db
    try:
        print("hit")
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if the user exists
        check_user_query = """
        SELECT COUNT(*) 
        FROM user 
        WHERE user_id = %s
        """
        cur.execute(check_user_query, (current_user.id,))
        user_exists = cur.fetchone()[0]
        # Error Message
        if user_exists == 0:
            return jsonify({"error": "User not found"}), 404

        # Select query
        select_user_studies_info_query = """
        SELECT 
            DATE_FORMAT(study.created_at, '%%m/%%d/%%Y') AS `Date_Created`,
            study.study_id AS `Study_ID`,
            study.study_name AS `User_Study_Name`,
            study.study_description AS `Description`,
            CONCAT(
                COALESCE(completed_sessions.completed_count, 0), 
                ' / ', 
                study.expected_participants
            ) AS `Sessions`,
            study_user_role_type.study_user_role_description AS `Role`
        FROM study
        INNER JOIN study_user_role
            ON study_user_role.study_id = study.study_id
        INNER JOIN study_user_role_type
            ON study_user_role.study_user_role_type_id = study_user_role_type.study_user_role_type_id
        LEFT JOIN (
            SELECT 
                study_id, 
                COUNT(*) AS completed_count
            FROM participant_session
            GROUP BY study_id
        ) AS completed_sessions
            ON study.study_id = completed_sessions.study_id
        WHERE study_user_role.user_id = %s
        """

        cur.execute(select_user_studies_info_query, (current_user.id,))
        # Get all rows
        results = cur.fetchall()
        # Close cursor
        cur.close()

        if not results:
            return jsonify({"message": "No studies found"}), 200

        return jsonify(results), 200

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


@bp.route("/api/copy_study", methods=["POST"])
@auth_required()
def copy_study():
    # Get JSON data from the request body
    submission_data = request.get_json()

    if not submission_data or "studyID" not in submission_data:
        return jsonify({"error": "Missing studyID in request body"}), 400

    study_id = submission_data["studyID"]
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if study exists
        check_study_query = """
        SELECT COUNT(*), study_name
        FROM study
        WHERE study_id = %s
        """
        cur.execute(check_study_query, (study_id,))
        study_results = cur.fetchone()

        if study_results[0] == 0:
            return jsonify({"error": "Study does not exist"}), 404

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
                current_user.id,
                study_id,
            ),
        )
        user_access_exists = cur.fetchone()

        # Error Message
        if user_access_exists is None:
            return jsonify({"error": "User does not have access to study"}), 404

        # Get the study data
        study_data = get_all_study_data_helper(study_id)

        # Give new study name
        study_count = study_results[0]
        study_data["studyName"] = study_results[1] + " (" + str(study_count) + ")"

        # Call the helper function to create the new study in the database
        new_study_id = create_study_data(study_data, current_user.id, cur)

        base_dir = current_app.config.get("RESULTS_BASE_DIR_PATH")

        consent_copy_status = copy_consent_form(study_id, new_study_id, cur, base_dir)
        if consent_copy_status == "failure":
            raise RuntimeError("Failed to copy consent form")

        for survey_type in ["pre", "post"]:
            survey_copy_status = copy_survey_form(
                study_id, new_study_id, cur, base_dir, survey_type
            )
            if survey_copy_status == "failure":
                raise RuntimeError(f"Failed to {survey_type} survey form")

        conn.commit()
        # Return success message
        return (
            jsonify({"message": "Study copied successfully", "study_id": new_study_id}),
            200,
        )

    except Exception as e:
        if "conn" in locals():
            conn.rollback()

        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


# This route is for loading ALL the detail on a single study, essentially rebuilding in reverse of how create_study deconstructs and saves into db
@bp.route("/api/load_study", methods=["POST"])
@auth_required()
def load_study():
    try:
        # Get the JSON data from the request body
        submission_data = request.get_json()

        if not submission_data or "studyID" not in submission_data:
            return jsonify({"error": "Missing studyID in request body"}), 400

        study_id = submission_data["studyID"]

        # Call the helper function to get the study data
        study_data = get_all_study_data_helper(study_id)

        return jsonify(study_data), 200

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        return jsonify({"error_type": error_type, "error_message": error_message}), 500


# Note, the study still exists in the database but not available to users
@bp.route("/api/delete_study", methods=["POST"])
@auth_required()
def delete_study():
    try:
        # Get the JSON data from the request body
        submission_data = request.get_json()

        if not submission_data or "studyID" not in submission_data:
            return jsonify({"error": "Missing studyID in request body"}), 400

        study_id = submission_data["studyID"]
        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if the user is the owner of the study
        check_owner_query = """
        SELECT COUNT(*)
        FROM study_user_role
        WHERE study_id = %s AND user_id = %s AND study_user_role_type_id = (
            SELECT study_user_role_type_id
            FROM study_user_role_type
            WHERE study_user_role_description = 'Owner'
        )
        """
        cur.execute(check_owner_query, (study_id, current_user.id))
        is_owner = cur.fetchone()[0]

        if is_owner == 0:
            return jsonify({"error": "Only the owner can delete the study"}), 403

        # Proceed with deletion if the user is the owner
        insert_deletion_query = """
        INSERT INTO deleted_study (study_id, deleted_by_user_id)
        VALUES (%s, %s)
        """
        cur.execute(insert_deletion_query, (study_id, current_user.id))

        # Copy study roles into deleted_study_role
        copy_roles_query = """
        INSERT INTO deleted_study_role (study_id, user_id, study_user_role_type_id)
        SELECT study_id, user_id, study_user_role_type_id
        FROM study_user_role
        WHERE study_id = %s
        """
        cur.execute(copy_roles_query, (study_id,))

        # Remove the study from study_user_role to prevent access
        delete_study_roles_query = "DELETE FROM study_user_role WHERE study_id = %s"
        cur.execute(delete_study_roles_query, (study_id,))

        # Commit the transaction
        conn.commit()

        # Close cursor
        cur.close()

        return jsonify({"message": "Study deleted successfully"}), 200

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500


@bp.route("/api/get_study_consent_form", methods=["POST"])
@auth_required()
def get_study_consent_form():
    try:
        data = request.get_json()

        # Check if study_id is provided
        if not data or "study_id" not in data:
            return jsonify({"error": "Missing study_id in request body"}), 400

        study_id = data["study_id"]
        conn = get_db_connection()
        cur = conn.cursor()

        consent_form_details_query = """
        SELECT
            file_path,
            original_filename
        FROM consent_form
        WHERE study_id = %s
        """
        cur.execute(consent_form_details_query, (study_id,))
        results = cur.fetchone()
        cur.close()

        # Study never had an assoc consent form which is okay
        if not results:
            return "", 204

        file_path, origin_filename = results

        # Db suggest a consent file should exist but could not retrieve one
        if not os.path.isfile(file_path):
            return jsonify({"error": "Consent form retrieval failed."}), 404

        response = send_file(file_path, mimetype="application/pdf", as_attachment=False)
        response.headers["X-Original-Filename"] = (
            origin_filename  # Need to rename file from filesystem convention to original
        )
        response.headers["Access-Control-Expose-Headers"] = "X-Original-Filename"
        return response

    except Exception as e:
        return jsonify({"error_type": type(e).__name__, "error_message": str(e)}), 500


@bp.route("/api/get_study_survey_form", methods=["POST"])
@auth_required()
def get_study_survey_form():
    try:
        data = request.get_json()

        # Check if study_id is provided
        if not data or "study_id" not in data or "survey_type" not in data:
            return (
                jsonify({"error": "Missing request parameters for survey retrieval"}),
                400,
            )

        study_id = data["study_id"]
        survey_type = data["survey_type"]

        if survey_type not in ["pre", "post"]:
            return jsonify({"error": "Invalid survey type received"}), 400

        conn = get_db_connection()
        cur = conn.cursor()

        survey_form_details_query = """
        SELECT
            file_path,
            original_filename
        FROM survey_form
        WHERE study_id = %s AND form_type = %s
        """
        cur.execute(survey_form_details_query, (study_id, survey_type))
        results = cur.fetchone()
        cur.close()

        # Study never had an assoc survey form which is okay
        if not results:
            return "", 204

        file_path, origin_filename = results

        # Db suggest a survey file should exist but could not retrieve one
        if not os.path.isfile(file_path):
            return (
                jsonify({"error": f"{survey_type} survey form retrieval failed."}),
                404,
            )

        response = send_file(
            file_path, mimetype="application/json", as_attachment=False
        )
        response.headers["X-Original-Filename"] = (
            origin_filename  # Need to rename file from filesystem convention to original
        )
        response.headers["Access-Control-Expose-Headers"] = "X-Original-Filename"
        return response

    except Exception as e:
        return jsonify({"error_type": type(e).__name__, "error_message": str(e)}), 500


# Validate survey uploads before allowing to save
@bp.route("/api/validate_survey_upload", methods=["POST"])
@auth_required()
def validate_survey_upload():
    try:
        survey_json = request.get_json()
        if not survey_json:
            return (
                jsonify(
                    {"error_type": "FileError", "error_message": "No JSON received."}
                ),
                400,
            )

        # High-level validation schema - Ref: https://builtin.com/software-engineering-perspectives/python-json-schema
        survey_schema = {
            "type": "object",
            "required": ["elements", "title", "description"],
            "properties": {
                "title": {"type": "string", "minLength": 1},
                "description": {"type": "string", "minLength": 1},
                "elements": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["type", "name", "title"],
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "text",
                                    "comment",
                                    "dropdown",
                                    "tagbox",
                                    "boolean",
                                    "checkbox",
                                    "rating",
                                ],
                            },
                            "name": {"type": "string", "minLength": 1},
                            "title": {"type": "string", "minLength": 1},
                        },
                    },
                },
            },
        }

        validate(instance=survey_json, schema=survey_schema)

        # Ensure no name duplicates since these are unique identifiers later
        used_names = set()
        for i, element in enumerate(survey_json["elements"]):
            name = element.get("name")
            if name in used_names:
                raise ValueError(f"Duplicate name found for question #{i+1}")
            used_names.add(name)

        return jsonify(survey_json), 200

    except ValidationError as ve:
        return (
            jsonify(
                {
                    "error_type": "ValidationError",
                    "error_message": ve.message,
                    "location": list(ve.path),
                }
            ),
            400,
        )

    except ValueError as ve:
        return jsonify({"error_type": "ValueError", "error_message": str(ve)}), 400

    except Exception as e:
        return jsonify({"error_type": type(e).__name__, "error_message": str(e)}), 400

# LEVI COME HERE
@bp.route("/api/get_study_data_by_id/<int:study_id>", methods=["GET"])
def get_study_data_by_id(study_id):
    # https://www.geeksforgeeks.org/read-json-file-using-python/
    # gets the json data from the db
    print(study_id)
    try:
        print("hit")
        conn = get_db_connection()
        cur = conn.cursor()

        # Check if the user exists
        # check_user_query = """
        # SELECT COUNT(*) 
        # FROM user 
        # WHERE user_id = %s
        # """
        # print("hit2")
        # cur.execute(check_user_query, study_id)
        # print("hit3")
        # user_exists = cur.fetchone()[0]
        # # Error Message
        # if user_exists == 0:
        #     return jsonify({"error": "User not found"}), 404

        # Select query
        select_user_studies_info_query = """
            SELECT
                s.study_id,
                s.study_name,
                s.study_description,
                sdt.study_design_type_description AS design_type,

                -- Total Tasks
                COUNT(DISTINCT t.task_id) AS total_tasks,

                -- Task Descriptions (ID + Description)
                GROUP_CONCAT(
                    DISTINCT CONCAT(t.task_id, ': ', t.task_description)
                    ORDER BY t.task_id
                    SEPARATOR '; '
                ) AS task_descriptions,

                -- Total Factors
                COUNT(DISTINCT f.factor_id) AS total_factors,

                -- Factor Descriptions (ID + Description)
                GROUP_CONCAT(
                    DISTINCT CONCAT(f.factor_id, ': ', f.factor_description)
                    ORDER BY f.factor_id
                    SEPARATOR '; '
                ) AS factor_descriptions,

                -- Total Trials
                COUNT(DISTINCT tr.trial_id) AS total_trials

            FROM study s

            LEFT JOIN study_design_type sdt
                ON sdt.study_design_type_id = s.study_design_type_id

            LEFT JOIN task t
                ON t.study_id = s.study_id

            LEFT JOIN factor f
                ON f.study_id = s.study_id

            LEFT JOIN trial tr
                ON tr.task_id = t.task_id
                AND tr.factor_id = f.factor_id

            WHERE s.study_id = %s
            GROUP BY s.study_id;

        """
        print("here2")
        cur.execute(select_user_studies_info_query, (study_id,))
        print("here3")
        # Get all rows
        results = cur.fetchall()
        # Close cursor
        cur.close()

        if not results:
            return jsonify({"message": "No studies found"}), 200

        return jsonify(results), 200

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # 500 means internal error, AKA the database probably broke
        return jsonify({"error_type": error_type, "error_message": error_message}), 500