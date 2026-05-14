"""
API routes for survey data access in analytics
"""

from flask import Blueprint, jsonify, current_app
import logging
import json
import os
from app.utility.db_connection import get_db_connection

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint for survey routes
analytics_surveys_bp = Blueprint(
    "analytics_surveys", __name__, url_prefix="/api/analytics"
)


@analytics_surveys_bp.route(
    "/participant-surveys/<int:study_id>/<int:participant_id>", methods=["GET"]
)
def get_participant_surveys(study_id, participant_id):
    """Get pre and post survey results for a specific participant"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get participant_session_id for this participant in this study
        cursor.execute(
            """
            SELECT ps.participant_session_id 
            FROM participant_session ps
            JOIN participant p ON ps.participant_id = p.participant_id
            WHERE p.participant_id = %s AND ps.study_id = %s
            LIMIT 1
        """,
            (participant_id, study_id),
        )

        session_result = cursor.fetchone()
        if not session_result:
            return jsonify({"error": "Participant session not found"}), 404

        participant_session_id = session_result[
            0
        ]  # Index-based access instead of dictionary

        # Get pre and post survey results
        cursor.execute(
            """
            SELECT sr.file_path, sf.form_type 
            FROM survey_results sr
            JOIN survey_form sf ON sr.survey_form_id = sf.survey_form_id
            WHERE sr.participant_session_id = %s
        """,
            (participant_session_id,),
        )

        survey_files = cursor.fetchall()

        # Load survey content from files
        survey_data = {"pre": None, "post": None}
        for survey in survey_files:
            try:
                file_path = survey[0]  # Index 0 = file_path
                form_type = survey[1]  # Index 1 = form_type

                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        survey_data[form_type] = json.load(f)
                        logger.info(f"Loaded {form_type} survey from {file_path}")
                else:
                    logger.warning(f"Survey file not found: {file_path}")
            except Exception as e:
                logger.error(f"Error loading survey file {file_path}: {str(e)}")

        return jsonify({"surveys": survey_data}), 200

    except Exception as e:
        logger.error(f"Error retrieving participant surveys: {str(e)}")
        return jsonify({"error": f"Failed to retrieve surveys: {str(e)}"}), 500


@analytics_surveys_bp.route("/survey-structure/<int:study_id>", methods=["GET"])
def get_survey_structure(study_id):
    """Get survey structure for a study"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the survey form paths for both pre and post surveys
        cursor.execute(
            """
            SELECT file_path, form_type 
            FROM survey_form 
            WHERE study_id = %s
        """,
            (study_id,),
        )

        survey_forms = cursor.fetchall()

        # Load survey structure from files
        survey_structure = {"pre": None, "post": None}
        for survey in survey_forms:
            try:
                file_path = survey[0]  # Index 0 = file_path
                form_type = survey[1]  # Index 1 = form_type

                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        survey_structure[form_type] = json.load(f)
                        logger.info(
                            f"Loaded {form_type} survey structure from {file_path}"
                        )
                else:
                    logger.warning(f"Survey file not found: {file_path}")
            except Exception as e:
                logger.error(f"Error loading survey file {file_path}: {str(e)}")

        return jsonify({"structure": survey_structure}), 200

    except Exception as e:
        logger.error(f"Error retrieving survey structure: {str(e)}")
        return jsonify({"error": f"Failed to retrieve survey structure: {str(e)}"}), 500


@analytics_surveys_bp.route(
    "/participant-demographics/<int:study_id>/<int:participant_id>", methods=["GET"]
)
def get_participant_demographics(study_id, participant_id):
    """Get demographic information for a specific participant"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get participant demographic data
        cursor.execute(
            """
            SELECT 
                p.age,
                gt.gender_description,
                het.highest_education_description,
                p.technology_competence
            FROM participant p
            JOIN participant_session ps ON p.participant_id = ps.participant_id
            JOIN gender_type gt ON p.gender_type_id = gt.gender_type_id
            JOIN highest_education_type het ON p.highest_education_type_id = het.highest_education_type_id
            WHERE ps.study_id = %s AND p.participant_id = %s
        """,
            (study_id, participant_id),
        )

        demo_result = cursor.fetchone()

        if not demo_result:
            return jsonify({"error": "Participant demographic data not found"}), 404

        # Get ethnicity data (which could be multiple values)
        cursor.execute(
            """
            SELECT et.ethnicity_description
            FROM participant_ethnicity pe
            JOIN ethnicity_type et ON pe.ethnicity_type_id = et.ethnicity_type_id
            WHERE pe.participant_id = %s
        """,
            (participant_id,),
        )

        ethnicity_results = cursor.fetchall()
        ethnicities = [e[0] for e in ethnicity_results]

        demographic_data = {
            "age": demo_result[0],
            "gender": demo_result[1],
            "education": demo_result[2],
            "techCompetency": demo_result[3],
            "ethnicity": ethnicities,
        }

        return jsonify({"demographics": demographic_data}), 200

    except Exception as e:
        logger.error(f"Error retrieving participant demographics: {str(e)}")
        return jsonify({"error": f"Failed to retrieve demographics: {str(e)}"}), 500
