# ==========================================
#                   imports
# ==========================================
# Libraries:
from fastapi import FastAPI
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
# Utils:
from utils.init_db import init_db
# API:
from api import main_router


# ==========================================
#                   main
# ==========================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# FastAPI object
app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT token middleware configuration
load_dotenv()

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required for session middleware")

# Routers
app.include_router(main_router)