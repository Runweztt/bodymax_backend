from functools import wraps
from flask import request, g, jsonify
from db import get_db


def require_auth(f):
    """Verify auth token via Supabase's get_user API — no JWT secret needed."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            return jsonify({"error": "Missing authorization token"}), 401
        try:
            db = get_db()
            user = db.auth.get_user(token)
            g.user_id = user.user.id
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated
