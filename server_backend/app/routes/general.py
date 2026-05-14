import json
from flask import Blueprint, jsonify, request
from app.utility.db_connection import get_db_connection
from flask_security import auth_required
from flask_login import current_user

bp = Blueprint("general", __name__)


# IMPORTANT: This is used to check if session still good
@bp.route("/api/ping", methods=["GET"])
@auth_required()
def ping():
    return jsonify({"message": "Pong!"}), 200


# Test Database Connection
@bp.route("/api/test_db")
@auth_required()
def test_db():
    # Convert all cookies into a dictionary (cookies are stored in request.cookies as a dictionary)
    cookies_dict = request.cookies

    # Convert the cookies dictionary to JSON string (for printing)
    cookies_json = json.dumps(
        cookies_dict, indent=4
    )  # Use indent=4 for pretty formatting

    # Print the JSON formatted cookies
    print("Cookies as JSON:")
    print(cookies_json)
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        test_query = """
        SELECT email
        FROM user
        WHERE user_id = %s
        """

        # Test query
        cur.execute(test_query, (current_user.id,))
        result = cur.fetchone()
        email = result[0]

        # Close the cursor
        cur.close()

        return jsonify(email), 200

    except Exception as e:
        # Error message
        return jsonify({"error": str(e)}), 500
