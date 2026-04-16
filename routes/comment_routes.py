from fastapi import APIRouter, Depends, HTTPException
from database import comments_collection
from models import CommentModel, CommentResponse
from auth import get_current_user
from bson import ObjectId
import datetime

router = APIRouter(prefix="/comments", tags=["Comments"])


def format_comment(c) -> dict:
    return {
        "id": str(c["_id"]),
        "username": c["username"],
        "content": c["content"],
        "likes": c.get("likes", 0),
        "liked_by": c.get("liked_by", []),
        "created_at": c.get("created_at", "")
    }


@router.get("/", response_model=list[CommentResponse])
async def get_comments():
    comments = []
    cursor = comments_collection.find().sort("created_at", -1)
    async for comment in cursor:
        comments.append(format_comment(comment))
    return comments


@router.post("/", response_model=CommentResponse)
async def post_comment(
    data: CommentModel,
    current_user: dict = Depends(get_current_user)
):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    new_comment = {
        "username": current_user["username"],
        "content": data.content.strip(),
        "likes": 0,
        "liked_by": [],
        "created_at": datetime.datetime.utcnow().isoformat()
    }

    result = await comments_collection.insert_one(new_comment)
    new_comment["_id"] = result.inserted_id
    return format_comment(new_comment)


@router.post("/{comment_id}/like", response_model=CommentResponse)
async def like_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        oid = ObjectId(comment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid comment ID")

    comment = await comments_collection.find_one({"_id": oid})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    username = current_user["username"]

    # Prevent liking own comment
    if comment["username"] == username:
        raise HTTPException(status_code=400, detail="You cannot like your own comment")

    # Prevent liking more than once
    if username in comment.get("liked_by", []):
        raise HTTPException(status_code=400, detail="You already liked this comment")

    await comments_collection.update_one(
        {"_id": oid},
        {
            "$inc": {"likes": 1},
            "$push": {"liked_by": username}
        }
    )

    updated = await comments_collection.find_one({"_id": oid})
    return format_comment(updated)