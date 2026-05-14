from flask import Blueprint, request, jsonify
from flask_security import auth_required, current_user, logout_user
from app import db
from app.utility.db_connection import get_db_connection

bp = Blueprint("user_handling", __name__)


# @bp.route("/api/accounts/change-email", methods=["POST"])
# #@auth_required()
# def change_email():
#     data = request.get_json()
#     new_email = data.get("email")
#     print(new_email)
#     if not new_email:
#         return jsonify({"error": "Email is required"}), 400

#     current_user.email = new_email
#     db.session.commit()

#     return jsonify({"message": "Email updated"}), 200


@bp.route("/api/accounts/update_user_profile", methods=["POST"])
@auth_required()
def update_user_profile():
    try:
        data = request.get_json()

        if data is None:
            return jsonify({"error": "Invalid or missing JSON body"}), 400

        query = """
            UPDATE user
            SET first_name = %s,
                last_name = %s,
                username = %s
            WHERE user_id = %s
        """
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            query,
            (
                data.get("first_name"),
                data.get("last_name"),
                data.get("username"),
                current_user.id,
            ),
        )
        conn.commit()
        cur.close()
        return jsonify({"message": "Profile updated"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Used for user searching emails to add user to study
@bp.route("/api/check_user_exists", methods=["POST"])
@auth_required()
def check_user_exists():
    # Get JSON data
    submission_data = request.get_json()

    if not submission_data or "desiredUserEmail" not in submission_data:
        return jsonify({"error": "Missing needed info for request body"}), 400

    desired_user_email = submission_data["desiredUserEmail"]
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        user_exists = """
        SELECT user_id
        FROM user
        WHERE user.email = %s
        """

        cur.execute(user_exists, (desired_user_email,))
        result = cur.fetchone()

        if result is None:
            return jsonify({"exists": "false"}), 200

        return jsonify({"exists": "true"}), 200

    except Exception as e:
        # Error message
        return jsonify({"error": str(e)}), 500


# This is the ping to check for auth, vue will use this to handle redirects
@bp.route("/api/accounts/get_user_profile_info", methods=["GET"])
@auth_required()
def get_user_profile_info():
    try:

        conn = get_db_connection()
        cur = conn.cursor()

        query = """
        SELECT email, first_name, last_name, username
        FROM user
        WHERE user_id = %s
        """

        cur.execute(query, (current_user.id,))
        result = cur.fetchone()

        # Close the cursor
        cur.close()

        if result:
            email, first_name, last_name, username = result
            return (
                jsonify(
                    {
                        "email": email,
                        "first_name": first_name,
                        "last_name": last_name,
                        "username": username,
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": "User not found"}), 404

    except Exception as e:
        # Error message
        return jsonify({"error": str(e)}), 500


@bp.route("/api/accounts/logout", methods=["POST"])
@auth_required()
def logout():
    try:
        logout_user()
        return jsonify({"message": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
