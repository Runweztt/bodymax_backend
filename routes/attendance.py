from flask import Blueprint, request, jsonify, g
from middleware.auth import require_auth
from middleware.idempotency import idempotent
from db import get_db
from datetime import date, datetime
from services.sms import checkin_sms

bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


@bp.get("/today")
@require_auth
def get_today():
    db = get_db()
    today = date.today().isoformat()

    # Get user profile to check role and branch
    user_res = db.table("profiles").select("role, branch_id").eq("id", g.user_id).single().execute()
    user_profile = user_res.data or {}
    role = user_profile.get("role", "Receptionist")
    user_branch = user_profile.get("branch_id")

    # Determine which branch to filter by (Strict Isolation for Receptionists)
    target_branch = None
    if role == "Receptionist":
        if user_branch:
            target_branch = user_branch
        else:
            return jsonify({"checkedInIds": [], "count": 0})
    else:
        target_branch = request.args.get("branch_id")

    # Query attendance
    if target_branch:
        # Fetch attendance for members of the specific branch
        result = db.table("attendance").select("member_id, members!inner(branch_id)").eq("attendance_date", today).eq("members.branch_id", target_branch).execute()
    else:
        result = db.table("attendance").select("member_id").eq("attendance_date", today).execute()

    ids = [r["member_id"] for r in result.data]
    return jsonify({"checkedInIds": ids, "count": len(ids)})


@bp.post("/checkin")
@require_auth
def checkin():
    db = get_db()
    body = request.get_json()
    member_id = body.get("memberId")
    if not member_id:
        return jsonify({"error": "memberId is required"}), 400

    today = date.today().isoformat()
    try:
        db.table("attendance").insert({
            "member_id": member_id,
            "attendance_date": today,
        }).execute()
        # Send check-in SMS
        member = db.table("members").select("full_name, phone").eq("id", member_id).single().execute()
        if member.data:
            checkin_sms(member.data["full_name"], member.data.get("phone"))
        return jsonify({"ok": True})
    except Exception as e:
        if "uq_attendance_member_date" in str(e):
            return jsonify({"ok": True, "already": True})
        return jsonify({"error": str(e)}), 500


@bp.delete("/checkin/<member_id>")
@require_auth
def remove_checkin(member_id):
    db = get_db()
    today = date.today().isoformat()
    db.table("attendance").delete().eq("member_id", member_id).eq("attendance_date", today).execute()
    return jsonify({"ok": True})


@bp.post("/daily-pass")
@require_auth
@idempotent
def daily_pass():
    db = get_db()
    body = request.get_json()
    today = date.today().isoformat()
    name = body.get("name", "Daily Pass Guest")
    branch_id = body.get("branchId")
    amount = body.get("amount", 2000) # Default daily pass fee
    payment_method = body.get("paymentMethod", "Cash")

    try:
        member = db.table("members").insert({
            "full_name": name,
            "category": "Daily Pass",
            "duration": "Daily",
            "start_date": today,
            "expiry_date": today,
            "status": "Active",
            "branch_id": branch_id
        }).execute()
        member_id = member.data[0]["id"]

        # Record Daily Pass Payment
        db.table("payments").insert({
            "member_id": member_id,
            "amount": amount,
            "payment_method": payment_method,
            "transaction_date": datetime.utcnow().isoformat()
        }).execute()

        db.table("attendance").insert({
            "member_id": member_id,
            "attendance_date": today,
        }).execute()

        return jsonify({"ok": True, "memberId": member_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
