from flask import Blueprint, jsonify
from middleware.auth import require_auth
from db import get_db
from datetime import datetime, timedelta

bp = Blueprint("finance", __name__, url_prefix="/api/finance")

MONTHS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


@bp.get("/stats")
@require_auth
def get_stats():
    db = get_db()
    result = db.table("payments").select("*").execute()
    payments = result.data
    if not payments:
        return jsonify({
            "revenue": 0, "transactions": 0,
            "monthlyData": [], "dailyData": [],
            "mobileRevenue": 0, "cashRevenue": 0,
        })

    total = sum(float(p["amount"]) for p in payments)

    # Monthly breakdown — last 10 months
    monthly_data = []
    now = datetime.utcnow()
    for i in range(10):
        d = datetime(now.year, now.month, 1) - timedelta(days=30 * (9 - i))
        m, y = d.month - 1, d.year
        rev = sum(
            float(p["amount"])
            for p in payments
            if p.get("transaction_date")
            and _parse(p["transaction_date"]).month - 1 == m
            and _parse(p["transaction_date"]).year == y
        )
        monthly_data.append({"month": MONTHS[m], "revenue": round(rev / 1000, 1)})

    # Daily breakdown — last 7 days
    daily_data = []
    today = datetime.utcnow().date()
    for i in range(7):
        d = today - timedelta(days=6 - i)
        day_str = d.isoformat()
        rev = sum(
            float(p["amount"])
            for p in payments
            if p.get("transaction_date") and p["transaction_date"].startswith(day_str)
        )
        daily_data.append({"day": DAYS[d.weekday()], "revenue": round(rev / 1000, 1)})

    mobile = sum(float(p["amount"]) for p in payments if p["payment_method"] == "Mobile Money")
    cash = sum(float(p["amount"]) for p in payments if p["payment_method"] == "Cash")

    return jsonify({
        "revenue": total,
        "transactions": len(payments),
        "monthlyData": monthly_data,
        "dailyData": daily_data,
        "mobileRevenue": mobile,
        "cashRevenue": cash,
    })


def _parse(iso_str):
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
