from flask import Blueprint, jsonify
from db import get_db
from middleware.auth import require_auth

bp = Blueprint("branches", __name__, url_prefix="/api")

@bp.get("/branches")
@require_auth
def list_branches():
    db = get_db()
    res = db.table("branches").select("*").order("name").execute()
    return jsonify(res.data or [])
