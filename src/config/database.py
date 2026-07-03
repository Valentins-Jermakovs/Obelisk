# =====================================================
#                       imports
# =====================================================
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
# =====================================================

# =====================================================
#       Load dotenv and get DATABASE_URL
# =====================================================
load_dotenv()                               # Read from .env
DATABASE_URL = os.getenv("DATABASE_URL")    # Save DATABASE_URL
# =====================================================


# =====================================================
#                   Engine creation
# =====================================================
engine = create_async_engine(
    DATABASE_URL,       # Engine URL
    echo=True,          # Log SQL queries for debugging (change to False in production)
)

# =====================================================
#           AsyncSessionLocal creation
# =====================================================
#   Create a session factory for async sessions
AsyncSessionLocal = sessionmaker(
    engine,                         # Engine
    class_=AsyncSession,            # Session class
    expire_on_commit=False          # Expire sessions after commit
)