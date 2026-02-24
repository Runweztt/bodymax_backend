from flask import Blueprint, request, jsonify, g
from middleware.auth import require_auth
from middleware.idempotency import idempotent
from db import get_db
from datetime import datetime, timedelta
from services.sms import welcome_sms, payment_sms
import base64
import uuid

bp = Blueprint("members", __name__, url_prefix="/api")


@bp.get("/branches")
def list_branches():
    db = get_db()
    result = db.table("branches").select("*").execute()
    return jsonify(result.data)


@bp.get("/members")
@require_auth
def list_members():
    db = get_db()
    # Get user profile to check role and branch
    user_res = db.table("profiles").select("role, branch_id").eq("id", g.user_id).single().execute()
    user_profile = user_res.data or {}
    role = user_profile.get("role", "Receptionist")
    user_branch = user_profile.get("branch_id")

    query = db.table("members").select("*")

    # Filter by branch if Receptionist (Strict Isolation)
    if role == "Receptionist":
        if user_branch:
            query = query.eq("branch_id", user_branch)
        else:
            # If a receptionist has no branch assigned, they see nothing
            return jsonify([])
    else:
        # Managers can filter by branch if provided in query params
        target_branch = request.args.get("branch_id")
        if target_branch:
            query = query.eq("branch_id", target_branch)

    result = query.execute()
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
    branch_id = body.get("branchId")
    photo_base64 = body.get("photo")

    if not full_name or not category:
        return jsonify({"error": "fullName and category are required"}), 400

    photo_url = None
    if photo_base64 and "," in photo_base64:
        try:
            # photo_base64 is expected to be "data:image/jpeg;base64,..."
            header, encoded = photo_base64.split(",", 1)
            file_data = base64.b64decode(encoded)
            file_ext = "jpg" # Defaulting to jpg as per CameraCapture
            file_name = f"{uuid.uuid4()}.{file_ext}"
            
            # Upload to Supabase Storage (member-photos bucket)
            # Note: The bucket must exist in Supabase
            res = db.storage.from_("member-photos").upload(
                path=file_name,
                file=file_data,
                file_options={"content-type": "image/jpeg"}
            )
            
            # Get public URL
            photo_url = db.storage.from_("member-photos").get_public_url(file_name)
        except Exception as e:
            print(f"Photo upload failed: {e}")
            # We continue even if photo upload fails, but log it

    # Generate Member Code if branch_id is provided
    member_code = None
    if branch_id:
        branch = db.table("branches").select("branch_code").eq("id", branch_id).single().execute()
        if branch.data:
            b_code = branch.data["branch_code"]
            # Count existing members in this branch for sequence
            count = db.table("members").select("id", count="exact").eq("branch_id", branch_id).execute()
            seq = (count.count or 0) + 1
            member_code = f"BM-{b_code}-{seq:03d}"

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
                "branch_id": branch_id,
                "member_code": member_code,
                "photo_url": photo_url
            })
            .execute()
        )
        member_data = member.data[0]

        # Send welcome SMS
        welcome_sms(full_name, body.get("phone"))

        if payment_method:
            base_price = body.get("amount", 30000)
            db.table("payments").insert({
                "member_id": member_data["id"],
                "amount": base_price,
                "payment_method": payment_method,
                "transaction_date": datetime.utcnow().isoformat()
            }).execute()
            # Send payment confirmation SMS
            payment_sms(full_name, body.get("phone"), base_price)

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
