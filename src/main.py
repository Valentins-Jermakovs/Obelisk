# ==========================================
#                   imports
# ==========================================
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from utils.init_db import init_db
from api import main_router
from fastapi.middleware.cors import CORSMiddleware
# ==========================================


# ==========================================
#                   main
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# FastAPI object
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware
load_dotenv()

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required for session middleware")

# Routers
app.include_router(main_router)
# ==========================================