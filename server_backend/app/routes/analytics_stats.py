#Routes: GET /api/analytics/<study_id>/stats (JSON) and GET /api/analytics/<study_id>/notebook (download)
from math import isfinite

from flask import Blueprint, jsonify, request

from app.utility.analytics.stats_engine import describe


bp = Blueprint("analytics_stats", __name__)


@bp.post("/api/stats/describe")
def describe_sample():
    """Summarize pasted numbers without reading or modifying study data."""
    payload = request.get_json(silent=True)
    text = payload.get("values") if isinstance(payload, dict) else None
    if not isinstance(text, str):
        return jsonify(error="Enter numbers separated by commas or whitespace."), 400
    if len(text) > 100_000:
        return jsonify(error="Enter at most 100,000 characters."), 400

    try:
        # Splitting on whitespace also accepts lines and tab-separated values.
        values = [float(token) for token in text.replace(",", " ").split()]
        if not values or not all(map(isfinite, values)):
            raise ValueError("Expected finite values")
        result = describe(values)
    except ValueError:
        return jsonify(error="Enter at least one number and use only finite numbers."), 400
    except OverflowError:
        return jsonify(error="These numbers are too large to summarize."), 400
    if any(isinstance(value, float) and not isfinite(value) for value in result.values()):
        return jsonify(error="These numbers are too large to summarize."), 400

    return jsonify(result)
