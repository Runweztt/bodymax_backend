from flask import Blueprint, jsonify
from middleware.auth import require_auth
from db import get_db
from datetime import datetime, timedelta
import random

bp = Blueprint("demo_data", __name__, url_prefix="/api/demo")


@bp.post("/generate")
@require_auth
def generate():
    db = get_db()
    result = db.table("members").select("id").limit(1).execute()
    if not result.data:
        return jsonify({"error": "No members found. Create a member first."}), 400
    member_id = result.data[0]["id"]

    existing = db.table("payments").select("id").execute()
    if existing.data:
        ids = [d["id"] for d in existing.data]
        db.table("payments").delete().in_("id", ids).execute()

    payments = []
    for i in range(7):
        count = random.randint(2, 5)
        for _ in range(count):
            d = datetime.utcnow() - timedelta(days=i)
            d = d.replace(hour=random.randint(8, 20), minute=random.randint(0, 59), second=0)
            payments.append({
                "member_id": member_id,
                "amount": random.randint(2000, 12000),
                "payment_method": "Mobile Money" if random.random() > 0.4 else "Cash",
                "transaction_date": d.isoformat(),
            })

    db.table("payments").insert(payments).execute()
    return jsonify({"ok": True, "count": len(payments)})
