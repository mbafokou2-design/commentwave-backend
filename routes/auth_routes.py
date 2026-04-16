from fastapi import APIRouter, HTTPException
from database import users_collection
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
    # Block registering as admin username
    if data.username.lower() == ADMIN_USERNAME.lower():
        raise HTTPException(status_code=400, detail="That username is not allowed")

    existing = await users_collection.find_one({"username": data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = {
        "username": data.username,
        "password": hash_password(data.password),
        "role": "user",
        "created_at": datetime.datetime.utcnow().isoformat()
    }

    await users_collection.insert_one(new_user)
    return {"message": "Account created successfully"}


@router.post("/login", response_model=TokenModel)
async def login(data: LoginModel):
    # Check if logging in as hardcoded admin
    if data.username == ADMIN_USERNAME and data.password == ADMIN_PASSWORD:
        token = create_access_token({
            "sub": ADMIN_USERNAME,
            "role": "admin"
        })
        return {"access_token": token, "token_type": "bearer"}

    # Regular user login
    user = await users_collection.find_one({"username": data.username})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({
        "sub": user["username"],
        "role": "user"
    })
    return {"access_token": token, "token_type": "bearer"}