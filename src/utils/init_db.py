# =====================================================
#                       imports
# =====================================================
# Libraries:
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
import os
# Models:
from models import (
    AuditLog,
    DimAuthor,
    DimBook,
    DimBookCopy,
    DimLibrary,
    DimLibrarian,
    DimReader,
    DimShelf,
    BookPosition,
    BookImage,
    LibrarianLibrary,
    FactLoan,
    BookAuthor,
    DimGenre,
    DimLanguage,
    BookGenre,
    BookLanguage
)
# =====================================================


# =====================================================
#                   .env initialization
# =====================================================

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None: 
    raise RuntimeError(".env file not found")

# Create engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)


# =====================================================
#                   DB initialization
# =====================================================
async def init_db():

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Database initialized")