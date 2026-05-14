from datetime import datetime, timedelta
import os
import random
from flask import Blueprint, jsonify
from app.utility.db_connection import get_db_connection

bp = Blueprint("testing_reset_db", __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the test file

# Go up one level to reach the root folder, then navigate to sql_database
CREATE_TABLES_SQL = os.path.join(BASE_DIR, "../../../sql_database", "create_tables.sql")
INSERT_DATA_SQL = os.path.join(
    BASE_DIR, "../../../sql_database/sample_data", "insert_all.sql"
)


def run_sql_file(cursor, file_path):
    with open(file_path, "r") as file:
        sql_statements = file.read()

    try:
        cursor.execute(sql_statements)
    except Exception as e:
        print(f"Error executing SQL file: {file_path}\n{e}")


@bp.route("/api/testing_reset_db", methods=["POST"])
def testing_reset_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check right database
        check_db_query = """SELECT DATABASE()"""
        cur.execute(check_db_query)

        current_db = cur.fetchone()[0]

        # Only works when __init__.py for create_app is in testing mode
        if current_db == "test_db":
            # Drop and recreate the test_db
            cur.execute("DROP DATABASE IF EXISTS test_db;")
            cur.execute("CREATE DATABASE test_db;")
            cur.execute("USE test_db;")  # Switch to test_db

            run_sql_file(cur, CREATE_TABLES_SQL)
            run_sql_file(cur, INSERT_DATA_SQL)

            conn.commit()

            return jsonify({"message": "test_db has been reset!"}), 200
        else:
            return jsonify({"error": "Current database is NOT the test database"}), 400

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # Return error response
        return (
            jsonify({"error_type": error_type, "error_message": error_message}),
            500,
        )


@bp.route("/api/testing_insert_participant_sessions", methods=["POST"])
def testing_insert_participant_sessions():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check right database
        check_db_query = """SELECT DATABASE()"""
        cur.execute(check_db_query)

        current_db = cur.fetchone()[0]

        # Only works when __init__.py for create_app is in testing mode
        if current_db == "test_db":

            for participant_id in range(1, 4):  # For 3 participants
                study_id = 1
                ended_at = (
                    datetime.now() + timedelta(minutes=random.randint(1, 60))
                ).strftime("%Y-%m-%d %H:%M:%S")

                # Generate random comments
                if participant_id == 1:
                    comments = "Participant is too smart. Terminate him"
                    is_valid = 0
                else:
                    comments = "They were very nice"
                    is_valid = 1

                # Generate the SQL INSERT statement
                insert_stmt = f"""
                    INSERT INTO participant_session (participant_id, study_id, ended_at, comments, is_valid)
                    VALUES ({participant_id}, {study_id}, '{ended_at}', '{comments}', {is_valid});
                """
                cur.execute(insert_stmt)
            conn.commit()
            return jsonify({"message": "test_db has been reset!"}), 200
        else:
            return jsonify({"error": "Current database is NOT the test database"}), 400
    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # Return error response
        return (
            jsonify({"error_type": error_type, "error_message": error_message}),
            500,
        )


@bp.route("/api/testing_update_database", methods=["POST"])
def testing_update_database(file_path, participant_id, measurement_option_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Check right database
        check_db_query = """SELECT DATABASE()"""
        cur.execute(check_db_query)

        current_db = cur.fetchone()[0]

        # Only works when __init__.py for create_app is in testing mode
        if current_db == "test_db":
            create_session_data_instance = f"""
                INSERT INTO session_data_instance (participant_session_id, task_id, measurement_option_id, factor_id)
                VALUES ({participant_id}, 1, {measurement_option_id}, {participant_id});
            """
            cur.execute(create_session_data_instance)
            conn.commit()

            cur.execute("SELECT LAST_INSERT_ID();")
            session_data_instance_id = cur.fetchone()[0]
            print(f"Last inserted session_data_instance_id: {session_data_instance_id}")

            # Update session_data_instance with the generated CSV path
            update_path_session_data_instance = f"""
                UPDATE session_data_instance 
                SET results_path = '{file_path}'
                WHERE session_data_instance_id = {session_data_instance_id};
            """
            cur.execute(update_path_session_data_instance)
            conn.commit()

            return (
                jsonify({"message": "session_data_instance updated successfully!"}),
                200,
            )
        else:
            return jsonify({"error": "Current database is NOT the test database"}), 400

    except Exception as e:
        # Error message
        error_type = type(e).__name__
        error_message = str(e)

        # Return error response
        return (
            jsonify({"error_type": error_type, "error_message": error_message}),
            500,
        )
