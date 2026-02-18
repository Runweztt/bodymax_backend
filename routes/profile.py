from flask import Blueprint, g, jsonify
from middleware.auth import require_auth
from db import get_db

bp = Blueprint("profile", __name__, url_prefix="/api")


@bp.get("/profile")
@require_auth
def get_profile():
    db = get_db()
    result = db.table("profiles").select("role").eq("id", g.user_id).single().execute()
    role = result.data.get("role", "Receptionist") if result.data else "Receptionist"
    return jsonify({"role": role})
