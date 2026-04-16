from pydantic import BaseModel
from typing import Optional, List

class RegisterModel(BaseModel):
    username: str
    password: str

class LoginModel(BaseModel):
    username: str
    password: str

class TokenModel(BaseModel):
    access_token: str
    token_type: str

class CommentModel(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: str
    username: str
    content: str
    likes: int
    liked_by: List[str] = []
    created_at: str