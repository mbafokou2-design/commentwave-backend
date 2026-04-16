from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth_routes import router as auth_router
from routes.comment_routes import router as comment_router
from routes.admin_routes import router as admin_router

app = FastAPI(title="CommentWave API", version="1.0.0")

# Allow React frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://commentwave-frontendhost.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(comment_router)
app.include_router(admin_router)

@app.get("/")
async def root():
    return {"message": "CommentWave API is running"}
