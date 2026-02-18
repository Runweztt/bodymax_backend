from flask import Blueprint, jsonify
from middleware.auth import require_auth
from db import get_db
from datetime import date, timedelta
from services.sms import expiry_sms

bp = Blueprint("expiry", __name__, url_prefix="/api/expiry")


@bp.post("/check")
@require_auth
def check_expiry():
    """Scan members expiring within 3 days and send SMS alerts."""
    db = get_db()
    today = date.today()
    cutoff = today + timedelta(days=3)

    result = (
        db.table("members")
        .select("id, full_name, phone, expiry_date, status")
        .lte("expiry_date", cutoff.isoformat())
        .gte("expiry_date", today.isoformat())
        .eq("status", "Active")
        .execute()
    )

    sent = 0
    skipped = 0
    for member in result.data:
        phone = member.get("phone")
        if not phone:
            skipped += 1
            continue
        days_left = (date.fromisoformat(member["expiry_date"]) - today).days
        expiry_sms(member["full_name"], phone, days_left)
        sent += 1

    # Also check already expired
    expired = (
        db.table("members")
        .select("id, full_name, phone, expiry_date")
        .lt("expiry_date", today.isoformat())
        .eq("status", "Active")
        .execute()
    )

    for member in expired.data:
        phone = member.get("phone")
        if not phone:
            skipped += 1
            continue
        expiry_sms(member["full_name"], phone, 0)
        sent += 1

    return jsonify({
        "sent": sent,
        "skipped_no_phone": skipped,
        "expiring_soon": len(result.data),
        "already_expired": len(expired.data),
    })
