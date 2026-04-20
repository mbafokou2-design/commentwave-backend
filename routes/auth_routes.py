from fastapi import APIRouter, HTTPException
from database import users_collection, banned_collection
from models import RegisterModel, LoginModel, TokenModel
from auth import hash_password, verify_password, create_access_token
from dotenv import load_dotenv
import os
import datetime

load_dotenv()

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
async def register(data: RegisterModel):
    if data.username.strip() == "":
        raise HTTPException(status_code=400, detail="Username cannot be empty")

    if data.username.lower() == ADMIN_USERNAME.lower():
        raise HTTPException(status_code=400, detail="That username is not allowed")

    if len(data.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    if len(data.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    existing = await users_collection.find_one({"username": data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = {
        "username":   data.username,
        "password":   hash_password(data.password),
        "role":       "user",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    await users_collection.insert_one(new_user)
    return {"message": "Account created successfully"}


@router.post("/login", response_model=TokenModel)
async def login(data: LoginModel):
    # Check if banned before even verifying password
    banned = await banned_collection.find_one({"username": data.username})
    if banned:
        raise HTTPException(
            status_code=403,
            detail=f"Your account has been banned. Reason: {banned.get('reason', 'Violation of rules')}"
        )

    # Admin hardcoded login
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        token = create_access_token({"sub": ADMIN_USERNAME, "role": "admin"})
        return {"access_token": token, "token_type": "bearer"}

    # Regular user
    user = await users_collection.find_one({"username": data.username})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": user["username"], "role": "user"})
    return {"access_token": token, "token_type": "bearer"}
