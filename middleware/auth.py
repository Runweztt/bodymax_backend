from functools import wraps
from flask import request, g, jsonify
from db import get_db


def require_auth(f):
    """Verify auth token via Supabase's get_user API."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token:
            print("[AUTH] No token provided")
            return jsonify({"error": "Missing authorization token"}), 401
        try:
            db = get_db()
            user = db.auth.get_user(token)
            g.user_id = user.user.id
            print(f"[AUTH] Authenticated user: {g.user_id}")
        except Exception as e:
            print(f"[AUTH] Token verification failed: {e}")
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated
