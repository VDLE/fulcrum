from collections import defaultdict
from flask import Blueprint, current_app, jsonify, request
from app.utility.db_connection import get_db_connection
from flask_security import auth_required

bp = Blueprint("trials", __name__)


from app.utility.permutations import (
    get_within_perm,
    get_between_perm,
    calc_perm_hash,
)


# Gets a new unique trial sequence (permutation)
@bp.route("/api/get_new_trials_perm", methods=["POST"])
@auth_required()
def get_new_trials_perm():
    try:
        data = request.get_json()
        study_id = data.get("study_id")
        perm_length = data.get("trial_count")

        if not study_id or not perm_length:
            return (
                jsonify({"error": "Missing study_id or trial_count in request"}),
                400,
            )

        if not perm_length:
            return (
                jsonify({"error": "Missing a requested trial count in the request"}),
                400,
            )

        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Finding trial seq used in previous sessions
        prior_sequences_query = """
        SELECT
            participant_session_id,
            task_id,
            factor_id
        FROM trial
        WHERE participant_session_id IN (
            SELECT participant_session_id
            FROM participant_session
            WHERE study_id = %s
        )
        ORDER BY trial.participant_session_id, started_at
        """
        cur.execute(prior_sequences_query, (study_id,))
        results = cur.fetchall()

        session_perms = defaultdict(list)
        for participant_session_id, task_id, factor_id in results:
            session_perms[participant_session_id].append((task_id, factor_id))

        # Converting each perm into a hash value to compare against later
        used_perms = set()
        for perm in session_perms.values():
            used_perms.add(calc_perm_hash(perm))

        # Get the study type
        get_study_type_query = """
        SELECT study_design_type_description
        FROM study_design_type
        JOIN study
        ON study_design_type.study_design_type_id = study.study_design_type_id
        WHERE study_id = %s
        """
        cur.execute(get_study_type_query, (study_id,))
        study_type = cur.fetchone()[0]

        # Get all task ids for study
        get_task_ids = """
        SELECT DISTINCT task_id
        FROM task
        WHERE study_id = %s
        """
        cur.execute(get_task_ids, (study_id,))
        task_list = [row[0] for row in cur.fetchall()]

        # Get all factor ids for study
        get_factor_ids = """
        SELECT DISTINCT factor_id
        FROM factor
        WHERE study_id = %s
        """
        cur.execute(get_factor_ids, (study_id,))
        factor_list = [row[0] for row in cur.fetchall()]

        if study_type == "Within":
            perm, status = get_within_perm(
                task_list, factor_list, perm_length, used_perms
            )
        elif study_type == "Between":
            perm, status = get_between_perm(
                task_list, factor_list, perm_length, used_perms
            )
        else:
            return jsonify({"error": "Invalid study type encountered"}), 400

        return jsonify({"new_perm": perm, "status_msg": status}), 200

    except Exception as e:
        return jsonify({"error_type": type(e).__name__, "error_message": str(e)}), 500


# Finding the number of trials in a study's most recent session to enforce consistency as new sessions are made
@bp.route("/api/previous_session_length", methods=["POST"])
@auth_required()
def previous_session_length():
    try:
        # Get the JSON data from the request body
        submission_data = request.get_json()

        if not submission_data or "studyID" not in submission_data:
            return jsonify({"error": "Missing studyID in request body"}), 400

        study_id = submission_data["studyID"]

        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Finding trials used in previous sessions
        previous_session_length_query = """
        SELECT COUNT(*) AS trial_count
        FROM trial
        WHERE participant_session_id = (
            SELECT participant_session_id
            FROM participant_session
            WHERE study_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        )
        """
        cur.execute(previous_session_length_query, (study_id,))
        result = cur.fetchone()[0]

        # No sessions yet for this study
        if result == 0:
            return jsonify({"prev_length": None}), 200

        else:
            return jsonify({"prev_length": result}), 200

    except Exception as e:
        return jsonify({"error_type": type(e).__name__, "error_message": str(e)}), 500


# Finds the number of times each trial (task-factor pair) has been tested under a given study
@bp.route("/api/get_trial_occurrences", methods=["POST"])
@auth_required()
def get_trial_occurrences():
    try:
        # Get the JSON data from the request body
        submission_data = request.get_json()
        if not submission_data or "study_id" not in submission_data:
            return jsonify({"error": "Missing study_id in request body"}), 400

        study_id = submission_data["study_id"]

        # Connect to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Finding trial sequences used in previous sessions
        prior_sequences_query = """
        SELECT
            t.task_name,
            f.factor_name
        FROM trial tr
        JOIN task t
        ON tr.task_id = t.task_id
        JOIN factor f
        ON tr.factor_id = f.factor_id
        WHERE tr.participant_session_id IN (
            SELECT participant_session_id
            FROM participant_session
            WHERE study_id = %s
        )
        """
        cur.execute(prior_sequences_query, (study_id,))
        results = cur.fetchall()

        # Counting trial appearances throughout the retrieved sequences
        matrix = defaultdict(lambda: defaultdict(int))
        for task_name, factor_name in results:
            matrix[task_name][factor_name] += 1

        res_matrix = {
            "matrix": {task: dict(factors) for task, factors in matrix.items()}
        }
        return jsonify(res_matrix)

    except Exception as e:
        return jsonify({"error_type": type(e).__name__, "error_message": str(e)}), 500
