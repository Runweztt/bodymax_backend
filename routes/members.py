from flask import Blueprint, request, jsonify
from middleware.auth import require_auth
from middleware.idempotency import idempotent
from db import get_db
from datetime import datetime, timedelta

bp = Blueprint("members", __name__, url_prefix="/api")


@bp.get("/members")
@require_auth
def list_members():
    db = get_db()
    result = db.table("members").select("*").execute()
    return jsonify(result.data)


@bp.post("/members")
@require_auth
@idempotent
def create_member():
    db = get_db()
    body = request.get_json()
    full_name = body.get("fullName")
    category = body.get("category")
    duration = body.get("duration")
    payment_method = body.get("paymentMethod")

    if not full_name or not category:
        return jsonify({"error": "fullName and category are required"}), 400

    duration_days = {"Weekly": 7, "Monthly": 30, "3 Months": 90, "Annual": 365}
    days = duration_days.get(duration, 30)
    start = datetime.utcnow().date()
    expiry = start + timedelta(days=days)

    try:
        member = (
            db.table("members")
            .insert({
                "full_name": full_name,
                "category": category,
                "duration": duration,
                "start_date": start.isoformat(),
                "expiry_date": expiry.isoformat(),
                "status": "Active",
                "phone": body.get("phone"),
                "email": body.get("email"),
            })
            .execute()
        )
        member_data = member.data[0]

        if payment_method:
            base_price = body.get("amount", 30000)
            db.table("payments").insert({
                "member_id": member_data["id"],
                "amount": base_price,
                "payment_method": payment_method,
            }).execute()

        return jsonify(member_data), 201

    except Exception as e:
        error_msg = str(e)
        if "idx_members_phone" in error_msg or "idx_members_email" in error_msg:
            return jsonify({"error": "A member with this phone or email already exists"}), 409
        return jsonify({"error": error_msg}), 500


@bp.delete("/members/<member_id>")
@require_auth
def delete_member(member_id):
    db = get_db()
    db.table("members").delete().eq("id", member_id).execute()
    return jsonify({"ok": True})
