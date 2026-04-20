from fastapi import APIRouter, Depends, HTTPException
from database import comments_collection
from models import CommentModel, CommentResponse, ReactionModel
from auth import get_current_user
from bson import ObjectId
import datetime

router = APIRouter(prefix="/comments", tags=["Comments"])


def format_comment(c) -> dict:
    return {
        "id":         str(c["_id"]),
        "username":   c["username"],
        "content":    c["content"],
        "likes":      c.get("likes", 0),
        "liked_by":   c.get("liked_by", []),
        "reactions":  c.get("reactions", []),
        "created_at": c.get("created_at", "")
    }


def parse_id(comment_id: str) -> ObjectId:
    try:
        return ObjectId(comment_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid comment ID")


# ── GET ALL ───────────────────────────────────────
@router.get("/", response_model=list[CommentResponse])
async def get_comments():
    comments = []
    cursor = comments_collection.find().sort("likes", -1)
    async for c in cursor:
        comments.append(format_comment(c))
    return comments


# ── POST COMMENT ──────────────────────────────────
@router.post("/", response_model=CommentResponse)
async def post_comment(
    data: CommentModel,
    current_user: dict = Depends(get_current_user)
):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    if len(data.content.strip()) > 500:
        raise HTTPException(status_code=400, detail="Comment cannot exceed 500 characters")

    new_comment = {
        "username":   current_user["username"],
        "content":    data.content.strip(),
        "likes":      0,
        "liked_by":   [],
        "reactions":  [],
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    result = await comments_collection.insert_one(new_comment)
    new_comment["_id"] = result.inserted_id
    return format_comment(new_comment)


# ── LIKE COMMENT ──────────────────────────────────
@router.post("/{comment_id}/like", response_model=CommentResponse)
async def like_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    oid     = parse_id(comment_id)
    comment = await comments_collection.find_one({"_id": oid})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    username = current_user["username"]

    if comment["username"] == username:
        raise HTTPException(status_code=400, detail="You cannot like your own comment")

    if username in comment.get("liked_by", []):
        raise HTTPException(status_code=400, detail="You already liked this comment")

    await comments_collection.update_one(
        {"_id": oid},
        {"$inc": {"likes": 1}, "$push": {"liked_by": username}}
    )
    updated = await comments_collection.find_one({"_id": oid})
    return format_comment(updated)


# ── REACT TO COMMENT ──────────────────────────────
@router.post("/{comment_id}/react", response_model=CommentResponse)
async def react_comment(
    comment_id: str,
    data: ReactionModel,
    current_user: dict = Depends(get_current_user)
):
    valid_emojis = ["👍", "❤️", "😂", "😮", "😢"]
    if data.emoji not in valid_emojis:
        raise HTTPException(status_code=400, detail="Invalid emoji reaction")

    oid     = parse_id(comment_id)
    comment = await comments_collection.find_one({"_id": oid})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    username  = current_user["username"]
    reactions = comment.get("reactions", [])

    # Remove existing reaction from this user if any
    reactions = [r for r in reactions if r.get("username") != username]

    # Add new reaction
    reactions.append({"username": username, "emoji": data.emoji})

    await comments_collection.update_one(
        {"_id": oid},
        {"$set": {"reactions": reactions}}
    )
    updated = await comments_collection.find_one({"_id": oid})
    return format_comment(updated)


# ── DELETE OWN COMMENT ────────────────────────────
@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    oid     = parse_id(comment_id)
    comment = await comments_collection.find_one({"_id": oid})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Only owner can delete their own comment
    if comment["username"] != current_user["username"]:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")

    await comments_collection.delete_one({"_id": oid})
    return {"message": "Comment deleted successfully"}
