from pydantic import BaseModel
from typing import Optional, List

# ── AUTH ──────────────────────────────────────────
class RegisterModel(BaseModel):
    username: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class TokenModel(BaseModel):
    access_token: str
    token_type: str

# ── COMMENTS ─────────────────────────────────────
class CommentModel(BaseModel):
    content: str

class ReactionModel(BaseModel):
    emoji: str

class CommentResponse(BaseModel):
    id: str
    username: str
    content: str
    likes: int
    liked_by: List[str] = []
    reactions: List[dict] = []
    created_at: str

# ── ADMIN ─────────────────────────────────────────
class BanModel(BaseModel):
    username: str
    reason: Optional[str] = "Banned by admin"
