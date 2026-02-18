from flask import Blueprint, request, jsonify
from middleware.auth import require_auth
from middleware.idempotency import idempotent
from db import get_db
from datetime import date

bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


@bp.get("/today")
@require_auth
def get_today():
    db = get_db()
    today = date.today().isoformat()
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
    name = body.get("name", "Daily Pass Guest")
    today = date.today().isoformat()

    try:
        member = db.table("members").insert({
            "full_name": name,
            "category": "Daily Pass",
            "duration": "Daily",
            "start_date": today,
            "expiry_date": today,
            "status": "Active",
        }).execute()
        member_id = member.data[0]["id"]

        db.table("attendance").insert({
            "member_id": member_id,
            "attendance_date": today,
        }).execute()

        return jsonify({"ok": True, "memberId": member_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
