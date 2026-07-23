# =====================================================
#                        Imports
# =====================================================

# Libraries:
from fastapi import FastAPI
from contextlib import asynccontextmanager
# from fastapi.middleware.cors import CORSMiddleware

# Utils:
from utils.init_db import init_db

# API:
from api import main_router


# =====================================================
#                        Main
# =====================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

# FastAPI object
app = FastAPI(lifespan=lifespan)



# CORS middleware
# Enable only when running FastAPI services directly without Nginx.
# In production, CORS is handled by the API Gateway (Nginx).
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins = [
#         "http://localhost:5173"
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



# Routers
app.include_router(main_router)