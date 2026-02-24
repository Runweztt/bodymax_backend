from flask import Blueprint, g, jsonify, request
from middleware.auth import require_auth
from db import get_db

bp = Blueprint("profile", __name__, url_prefix="/api")


@bp.get("/profile")
@require_auth
def get_profile():
    db = get_db()
    result = db.table("profiles").select("role, branch_id").eq("id", g.user_id).single().execute()
    if not result.data:
        return jsonify({"role": "Receptionist", "branch_id": None})
    return jsonify({
        "role": result.data.get("role", "Receptionist"),
        "branch_id": result.data.get("branch_id")
    })


@bp.post("/signup")
def signup():
    db = get_db()
    body = request.get_json()
    email = body.get("email")
    password = body.get("password")
    branch_id = body.get("branch_id")

    if not email or not password or not branch_id:
        return jsonify({"error": "Email, password, and branch_id are required"}), 400

    try:
        # 1. Create user in Supabase Auth
        auth_res = db.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })
        
        if not auth_res.user:
            return jsonify({"error": "Auth user creation failed"}), 500
        
        user_id = auth_res.user.id

        # 2. Create profile entry
        db.table("profiles").insert({
            "id": user_id,
            "role": "Receptionist",
            "branch_id": branch_id
        }).execute()

        return jsonify({"ok": True, "userId": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
