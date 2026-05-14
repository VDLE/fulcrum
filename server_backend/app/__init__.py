# This file initializes the flask app configuration
from flask import Flask
from flask_cors import CORS
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_security import (
    Security,
    SQLAlchemyUserDatastore,
)
from flask_security.models import fsqla_v3 as fsqla
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from flask_mailman import Mail
from flask_security import MailUtil
import os
from app.utility.user_serializer import user_serializer

mysql = MySQL()
db = SQLAlchemy()  # Only for user tracking via Flask-Security
csrf = CSRFProtect()

# Confirmation email when registering
mail = Mail()

import logging

logging.basicConfig(level=logging.DEBUG)


def create_app(testing=False):
    # Creating app
    app = Flask(__name__)
    app.config.from_object(__name__)

    # Load environment variables
    load_dotenv()
    
    print(os.path.abspath(os.path.dirname(__file__)))

    # MYSQL Configuration
    app.config["MYSQL_HOST"] = os.getenv("MYSQL_HOST")
    app.config["MYSQL_USER"] = os.getenv("MYSQL_USER")
    app.config["MYSQL_PASSWORD"] = os.getenv("MYSQL_PASSWORD")
    app.config["VUE_APP_BACKEND_URL"] = os.getenv("VUE_APP_BACKEND_URL")
    app.config["VUE_APP_BACKEND_PORT"] = os.getenv("VUE_APP_BACKEND_PORT")
    if testing:
        app.config["MYSQL_DB"] = "test_db"
    else:
        app.config["MYSQL_DB"] = os.getenv("MYSQL_DB").strip()
    mysql.init_app(app)

    # Server CSV pathway configuration
    app.config["RESULTS_BASE_DIR_PATH"] = os.getenv("RESULTS_BASE_DIR_PATH", "/app/data/participants_results")
    app.config["TRACKING_TOOL_DIR_PATH"] = os.getenv("TRACKING_TOOL_DIR_PATH", "/app/data/tracking_tool_downloads")

    # Flask-Security configs
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    # app.config["SECURITY_PASSWORD_HASH"] = "argon2"
    app.config["SECURITY_PASSWORD_SALT"] = os.getenv("SECRET_PASSWORD_SALT")

    # Customized settings so that VUE can be used instead of default server-side html rendering via Flask Security
    app.config["SECURITY_FLASH_MESSAGES"] = False
    app.config["SECURITY_URL_PREFIX"] = "/api/accounts"

    app.config["SECURITY_RECOVERABLE"] = True
    app.config["SECURITY_TRACKABLE"] = True
    app.config["SECURITY_CHANGEABLE"] = True
    app.config["SECURITY_CONFIRMABLE"] = True
    app.config["SECURITY_REGISTERABLE"] = True
    app.config["SEND_REGISTER_EMAIL"] = True
    app.config["SECURITY_UNIFIED_SIGNIN"] = False

    app.config["SECURITY_POST_CONFIRM_VIEW"] = (
        os.getenv("EXPECTED_FRONTEND_DOMAIN_URL", "http://localhost:5173")
        + "/confirmed"
    )  # Update this when frontend deployed
    app.config["SECURITY_CONFIRM_ERROR_VIEW"] = (
        os.getenv("EXPECTED_FRONTEND_DOMAIN_URL", "http://localhost:5173")
        + "/confirmed"
    )  # Update this when frontend deployed
    app.config["SECURITY_RESET_VIEW"] = "/reset-password"
    app.config["SECURITY_RESET_ERROR_VIEW"] = "/reset-password-error"
    app.config["SECURITY_LOGIN_ERROR_VIEW"] = "/login-error"
    app.config["SECURITY_POST_OAUTH_LOGIN_VIEW"] = "/post-oauth-login"
    app.config["SECURITY_REDIRECT_BEHAVIOR"] = "spa"

    app.config["SECURITY_CSRF_PROTECT_MECHANISMS"] = ["session", "basic"]
    app.config["SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS"] = True

    app.config["SECURITY_CSRF_COOKIE_NAME"] = "XSRF-TOKEN"
    app.config["SECURITY_CSRF_COOKIE_HTTPONLY"] = False
    app.config["WTF_CSRF_CHECK_DEFAULT"] = False
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    app.config["SESSION_TYPE"] = "filesystem"  # Store sessions in the filesystem
    app.config["SESSION_PERMANENT"] = (
        True  # Make session cookies expire when browser closes
    )
    app.config["SESSION_COOKIE_NAME"] = "session"
    app.config["SESSION_COOKIE_HTTPONLY"] = (
        False  # Prevent JavaScript from accessing session cookie
    )
    app.config["SESSION_COOKIE_SECURE"] = (
        False  # Requires HTTPS, change to False for local dev
    )
    app.config["SESSION_COOKIE_SAMESITE"] = (
        "Lax"  # Adjust if cross-origin issues occur. This is lax cuz of the vue proxy
    )
    
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")
    app.config["MAIL_TIMEOUT"] = int(os.getenv("MAIL_TIMEOUT", 10))
    app.config["SECURITY_CONFIRM_EMAIL_CHANGE"] = True
    app.config["SECURITY_EMAIL_SUBJECT_CHANGE_NOTICE"] = (
        "Confirm your new Fulcrum email"
    )

    # app.config["MAIL_BACKEND"] = "console"  # USE THIS ONLY WHEN DEBUGGING THE EMAIL
    app.config["SECURITY_USER_IDENTITY_ATTRIBUTES"] = [
        {"email": {"mapper": "email", "primary": True}}
    ]

    mail.init_app(app)

    app.config["SECURITY_JSON"] = True  # Forces JSON responses instead of HTML
    app.config["SECURITY_TOKEN_AUTHENTICATION_ENABLED"] = True
    app.config["SECURITY_API_ENABLE_TOKEN_AUTH"] = (
        True  # Needed to return token in login response
    )
    app.config["SECURITY_TOKEN_AUTHENTICATION_HEADER"] = "Authentication-Token"
    app.config["SECURITY_TOKEN_AUTHENTICATION_KEY"] = "auth_token"
    app.config["SECURITY_TOKEN_MAX_AGE"] = 3600  # Optional, token TTL in seconds
    app.config["SECURITY_USER_SERIALIZER"] = "utility.user_serializer.user_serializer"

    # SQLAlchemy ONLY for Flask-Security
    # This is done since Flask-Security is easy to use when using an ORM
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DB').strip()}"
    )
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    csrf.init_app(app)
    # fsqla.FsModels.set_db_info(db)

    # Import models
    from security.models import User, Role

    # fsqla.FsModels.set_db_info(db, user_model=User, role_model=Role)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)

    security = Security(app, user_datastore)
    with app.app_context():
        db.create_all()

        for rule in app.url_map.iter_rules():
            if "change" in rule.rule:
                print(f"[DEBUG] Registered route: {rule.rule} -> {rule.endpoint}")
    CORS(
        app,
        resources={r"/*": {"origins": {os.getenv("EXPECTED_FRONTEND_DOMAIN_URL")}}},
        expose_headers=[
            "Content-Disposition",
            "Content-Type",
            "X-CSRFToken",
            "Authorization",
            "Authentication-Token",
            "XSRF-TOKEN",
        ],
        supports_credentials=True,
    )

    # Register blueprints
    from app.routes.general import bp as general_bp
    from app.routes.studies import bp as studies_bp
    from app.routes.sessions import bp as sessions_bp
    from app.routes.testing_reset_db import bp as testing_reset_db_bp
    from app.routes.user_handling import bp as user_handling
    from app.routes.trials import bp as trials_bp
    from app.routes.downloads import bp as downloads_bp

    # Import analytics blueprint and init functions
    from app.routes.analytics import analytics_bp

    # Import analytics surveys blueprint
    from app.routes.analytics_surveys import analytics_surveys_bp

    app.register_blueprint(general_bp)
    app.register_blueprint(studies_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(testing_reset_db_bp)
    app.register_blueprint(user_handling)
    app.register_blueprint(trials_bp)
    app.register_blueprint(downloads_bp)

    # Register analytics blueprint last so initialization has already happened
    app.register_blueprint(analytics_bp)
    # Register analytics surveys blueprint
    app.register_blueprint(analytics_surveys_bp)

    # Log that analytics blueprint was registered
    app.logger.info("Analytics API routes registered")
    app.logger.info("Analytics surveys API routes registered")

    return app
