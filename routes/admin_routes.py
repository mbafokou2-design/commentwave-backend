from fastapi import APIRouter, Depends, HTTPException
from database import comments_collection, users_collection, banned_collection
from models import BanModel
from auth import require_admin
from bson import ObjectId
import datetime

router = APIRouter(prefix="/admin", tags=["Admin"])


def parse_id(comment_id: str) -> ObjectId:
    try:
        return ObjectId(comment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid comment ID")


# ── FULL STATS ────────────────────────────────────
@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(require_admin)):
    # Total users
    total_users = await users_collection.count_documents({})

    # All usernames + banned status
    all_users = []
    banned_list = []
    async for u in users_collection.find({}, {"username": 1, "_id": 0}):
        all_users.append(u["username"])

    async for b in banned_collection.find({}, {"username": 1, "reason": 1, "_id": 0}):
        banned_list.append({
            "username": b["username"],
            "reason":   b.get("reason", "No reason")
        })

    # Most liked comment
    top_comment = None
    async for doc in comments_collection.find().sort("likes", -1).limit(1):
        top_comment = {
            "id":       str(doc["_id"]),
            "username": doc["username"],
            "content":  doc["content"],
            "likes":    doc.get("likes", 0)
        }

    # Top user by total likes
    pipeline = [
        {"$group": {
            "_id":           "$username",
            "total_likes":   {"$sum": "$likes"},
            "comment_count": {"$sum": 1}
        }},
        {"$sort": {"total_likes": -1}},
        {"$limit": 1}
    ]
    top_user = None
    async for doc in comments_collection.aggregate(pipeline):
        top_user = {
            "username":      doc["_id"],
            "total_likes":   doc["total_likes"],
            "comment_count": doc["comment_count"]
        }

    return {
        "total_users": total_users,
        "all_users":   all_users,
        "banned_users": banned_list,
        "top_comment": top_comment,
        "top_user":    top_user
    }


# ── ADMIN DELETE ANY COMMENT ──────────────────────
@router.delete("/comments/{comment_id}")
async def admin_delete_comment(
    comment_id: str,
    current_user: dict = Depends(require_admin)
):
    oid     = parse_id(comment_id)
    comment = await comments_collection.find_one({"_id": oid})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    await comments_collection.delete_one({"_id": oid})
    return {"message": f"Comment by {comment['username']} deleted by admin"}


# ── BAN USER ──────────────────────────────────────
@router.post("/ban")
async def ban_user(
    data: BanModel,
    current_user: dict = Depends(require_admin)
):
    # Cannot ban admin
    from dotenv import load_dotenv
    import os
    load_dotenv()
    if data.username == os.getenv("ADMIN_USERNAME"):
        raise HTTPException(status_code=400, detail="Cannot ban the admin account")

    # Check user exists
    user = await users_collection.find_one({"username": data.username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check already banned
    already = await banned_collection.find_one({"username": data.username})
    if already:
        raise HTTPException(status_code=400, detail="User is already banned")

    await banned_collection.insert_one({
        "username":   data.username,
        "reason":     data.reason,
        "banned_at":  datetime.datetime.utcnow().isoformat()
    })
    return {"message": f"{data.username} has been banned"}


# ── UNBAN USER ────────────────────────────────────
@router.post("/unban")
async def unban_user(
    data: BanModel,
    current_user: dict = Depends(require_admin)
):
    banned = await banned_collection.find_one({"username": data.username})
    if not banned:
        raise HTTPException(status_code=404, detail="User is not banned")

    await banned_collection.delete_one({"username": data.username})
    return {"message": f"{data.username} has been unbanned"}
