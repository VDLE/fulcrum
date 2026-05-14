import io
import os
import zipfile
from flask import Blueprint, current_app, jsonify, send_file
from flask_security import auth_required

bp = Blueprint("downloads", __name__)

# Files/dirs we never want shipping inside the tracking-tool ZIP.
_EXCLUDED_DIRS = {"__pycache__", "tests", ".pytest_cache", ".venv", "venv"}
_EXCLUDED_SUFFIXES = (".pyc", ".pyo")


@bp.route("/api/download_tracking_tool", methods=["POST"])
@auth_required()
def download_tracking_tool():
    try:
        src_dir = current_app.config.get("TRACKING_TOOL_SRC_DIR", "/app/local_backend")
        if not os.path.isdir(src_dir):
            return jsonify({"error": "Tracking tool source not found."}), 404

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(src_dir):
                dirs[:] = [d for d in dirs if d not in _EXCLUDED_DIRS]
                for fname in files:
                    if fname.endswith(_EXCLUDED_SUFFIXES):
                        continue
                    fpath = os.path.join(root, fname)
                    arcname = os.path.join(
                        "FulcrumTrackingTool",
                        os.path.relpath(fpath, src_dir),
                    )
                    zf.write(fpath, arcname)
        buf.seek(0)

        return send_file(
            buf,
            as_attachment=True,
            download_name="FulcrumTrackingTool.zip",
            mimetype="application/zip",
        )

    except Exception as e:
        print(f"Error sending tracking tool: {e}")
        return jsonify({"error_type": type(e).__name__, "error_message": str(e)}), 500
