from flask import Blueprint, jsonify, g, request
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
            return jsonify({
                "revenue": 0, "transactions": 0,
                "monthlyData": [], "dailyData": [],
                "mobileRevenue": 0, "cashRevenue": 0,
            })
    else:
        target_branch = request.args.get("branch_id")
        # Sanitize target_branch from frontend JS 'null'/'undefined'
        if target_branch in ["null", "undefined", ""]:
            target_branch = None
    
    # Query payments & expenses - if branch filter is active, we need to join with members
    if target_branch:
        # Fetch payments for members of the specific branch
        p_res = db.table("payments").select("*, members!inner(branch_id)").eq("members.branch_id", target_branch).execute()
        # Fetch expenses for the specific branch
        e_res = db.table("expenses").select("*").eq("branch_id", target_branch).execute()
    else:
        p_res = db.table("payments").select("*").execute()
        e_res = db.table("expenses").select("*").execute()
    
    payments = p_res.data or []
    expenses = e_res.data or []

    total_revenue = sum(float(p["amount"]) for p in payments)
    total_expenses = sum(float(e["amount"]) for e in expenses)
    net_profit = total_revenue - total_expenses

    # Monthly breakdown — last 10 months (Revenue vs Expenses)
    monthly_data = []
    now = datetime.utcnow()
    for i in range(10):
        d = datetime(now.year, now.month, 1) - timedelta(days=30 * (9 - i))
        m, y = d.month - 1, d.year
        
        rev = sum(float(p["amount"]) for p in payments 
                 if p.get("transaction_date") and _parse(p["transaction_date"]).month - 1 == m and _parse(p["transaction_date"]).year == y)
        exp = sum(float(e["amount"]) for e in expenses 
                 if e.get("date") and datetime.fromisoformat(e["date"]).month - 1 == m and datetime.fromisoformat(e["date"]).year == y)
        
        monthly_data.append({
            "month": MONTHS[m], 
            "revenue": round(rev / 1000, 1),
            "expenses": round(exp / 1000, 1)
        })

    # Daily breakdown — last 7 days
    daily_data = []
    today = datetime.utcnow().date()
    for i in range(7):
        d = today - timedelta(days=6 - i)
        day_str = d.isoformat()
        rev = sum(float(p["amount"]) for p in payments if p.get("transaction_date") and p["transaction_date"].startswith(day_str))
        exp = sum(float(e["amount"]) for e in expenses if e.get("date") == day_str)
        
        daily_data.append({
            "day": DAYS[d.weekday()], 
            "revenue": round(rev / 1000, 1),
            "expenses": round(exp / 1000, 1)
        })

    mobile = sum(float(p["amount"]) for p in payments if p["payment_method"] == "Mobile Money")
    cash = sum(float(p["amount"]) for p in payments if p["payment_method"] == "Cash")

    # Group expenses by category
    expense_categories = {}
    for e in expenses:
        cat = e.get("category", "General")
        expense_categories[cat] = expense_categories.get(cat, 0) + float(e["amount"])

    return jsonify({
        "revenue": total_revenue,
        "expenses": total_expenses,
        "netProfit": net_profit,
        "transactions": len(payments),
        "monthlyData": monthly_data,
        "dailyData": daily_data,
        "mobileRevenue": mobile,
        "cashRevenue": cash,
        "expenseCategories": [{"name": k, "value": v} for k, v in expense_categories.items()]
    })


def _parse(iso_str):
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
