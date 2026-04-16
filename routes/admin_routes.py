from fastapi import APIRouter, Depends
from database import comments_collection, users_collection
from auth import require_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(require_admin)):

    # Total users
    total_users = await users_collection.count_documents({})

    # All usernames
    all_users = []
    async for user in users_collection.find({}, {"username": 1, "_id": 0}):
        all_users.append(user["username"])

    # Most liked comment
    top_comment = None
    cursor = comments_collection.find().sort("likes", -1).limit(1)
    async for doc in cursor:
        top_comment = {
            "id": str(doc["_id"]),
            "username": doc["username"],
            "content": doc["content"],
            "likes": doc.get("likes", 0)
        }

    # Top user by total likes
    pipeline = [
        {"$group": {
            "_id": "$username",
            "total_likes": {"$sum": "$likes"},
            "comment_count": {"$sum": 1}
        }},
        {"$sort": {"total_likes": -1}},
        {"$limit": 1}
    ]
    top_user = None
    async for doc in comments_collection.aggregate(pipeline):
        top_user = {
            "username": doc["_id"],
            "total_likes": doc["total_likes"],
            "comment_count": doc["comment_count"]
        }

    return {
        "total_users": total_users,
        "all_users": all_users,
        "top_comment": top_comment,
        "top_user": top_user
    }