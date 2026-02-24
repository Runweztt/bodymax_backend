from flask import Blueprint, request, jsonify, g
from db import get_db
from routes.profile import require_auth

bp = Blueprint("expenses", __name__, url_prefix="/api")


@bp.get("/expenses")
@require_auth
def list_expenses():
    db = get_db()
    
    # Fetch profile for role/branch
    user_res = db.table("profiles").select("role, branch_id").eq("id", g.user_id).single().execute()
    user_profile = user_res.data or {}
    role = user_profile.get("role", "Receptionist")
    user_branch = user_profile.get("branch_id")

    query = db.table("expenses").select("*, profiles!recorded_by(email)")

    # Strict isolation for receptionists
    if role == "Receptionist":
        if user_branch:
            query = query.eq("branch_id", user_branch)
        else:
            return jsonify([])
    else:
        # Managers can filter by branch
        target_branch = request.args.get("branch_id")
        if target_branch in ["null", "undefined", ""]:
            target_branch = None
            
        if target_branch:
            query = query.eq("branch_id", target_branch)

    result = query.order("date", desc=True).limit(100).execute()
    return jsonify(result.data or [])


@bp.post("/expenses")
@require_auth
def add_expense():
    db = get_db()
    
    # Fetch profile for role/branch
    user_res = db.table("profiles").select("role, branch_id").eq("id", g.user_id).single().execute()
    user_profile = user_res.data or {}
    role = user_profile.get("role", "Receptionist")
    user_branch = user_profile.get("branch_id")
    
    body = request.get_json()

    description = body.get("description")
    amount = body.get("amount")
    category = body.get("category", "General")
    branch_id = body.get("branch_id")
    date = body.get("date")

    if not description or not amount or not branch_id:
        return jsonify({"error": "Description, amount, and branch_id are required"}), 400

    # Role-based restriction: Receptionists can ONLY record for their own branch
    if role == "Receptionist":
        if str(branch_id) != str(user_branch):
            return jsonify({"error": "Unauthorized branch access"}), 403

    try:
        data = {
            "description": description,
            "amount": float(amount),
            "category": category,
            "branch_id": branch_id,
            "recorded_by": g.user_id,
        }
        if date:
            data["date"] = date

        res = db.table("expenses").insert(data).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.delete("/expenses/<id>")
@require_auth
def delete_expense(id):
    db = get_db()
    
    # Fetch profile for role/branch
    user_res = db.table("profiles").select("role, branch_id").eq("id", g.user_id).single().execute()
    user_profile = user_res.data or {}
    role = user_profile.get("role", "Receptionist")
    user_branch = user_profile.get("branch_id")

    # Verify ownership or manager role
    expense = db.table("expenses").select("recorded_by, branch_id").eq("id", id).single().execute()
    if not expense.data:
        return jsonify({"error": "Expense not found"}), 404

    if role == "Receptionist":
        if expense.data["recorded_by"] != g.user_id:
            return jsonify({"error": "Only creators or managers can delete expenses"}), 403

    try:
        db.table("expenses").delete().eq("id", id).execute()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
