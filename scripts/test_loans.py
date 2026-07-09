import asyncio
import sys
from sqlmodel import SQLModel, create_engine
import os

# Ensure project 'src' is importable
sys.path.append("src")

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

# Import models and services
import models  # noqa: F401 - ensures all model classes are loaded into metadata
from models import (
    DimLibrary,
    DimShelf,
    DimReader,
    DimBook,
    DimBookCopy,
    BookPosition,
    DimLibrarian,
    LibrarianLibrary,
)
from schemas.loan import LoanCreate, LoanUpdate
from models import LoanStatus
from services.loan_service import create_loan, update_loan, delete_loan

DB_PATH = "/tmp/obelisk_test.db"
SYNC_URL = f"sqlite:///{DB_PATH}"
ASYNC_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Ensure old test DB removed, then create sync engine and create tables
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

sync_engine = create_engine(SYNC_URL)
SQLModel.metadata.create_all(sync_engine)

async def main():
    async_engine = create_async_engine(ASYNC_URL, echo=False)
    AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as session:
        # Create library
        lib = DimLibrary(name="Test Library", city="TestCity", address="Test Address")
        session.add(lib)
        await session.commit()
        await session.refresh(lib)

        # Create shelf
        shelf = DimShelf(library_id=lib.id, code="A-01", section="S1")
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        # Create reader
        reader = DimReader(full_name="John Reader", email="reader@example.com")
        session.add(reader)
        await session.commit()
        await session.refresh(reader)

        # Create book
        book = DimBook(title="Test Title", isbn="ISBN-1234", publication_year=2020)
        session.add(book)
        await session.commit()
        await session.refresh(book)

        # Create book copy
        copy = DimBookCopy(book_id=book.id, inventory_code="INV-1")
        session.add(copy)
        await session.commit()
        await session.refresh(copy)

        # Position
        pos = BookPosition(book_copy_id=copy.id, shelf_id=shelf.id, row=1, column=1)
        session.add(pos)
        await session.commit()

        # Create librarian and assign to library
        libn = DimLibrarian(full_name="Lib One", email="lib@example.com")
        session.add(libn)
        await session.commit()
        await session.refresh(libn)

        assign = LibrarianLibrary(librarian_id=libn.id, library_id=lib.id)
        session.add(assign)
        await session.commit()

        # Prepare payload
        payload = {"roles": ["librarian"], "email": "lib@example.com"}

        # Create loan
        data = LoanCreate(book_copy_id=copy.id, reader_id=reader.id, library_id=lib.id)
        loan = await create_loan(session=session, data=data, payload=payload)
        print("Created loan:", loan["id"], loan["book"]["id"], loan["reader"]["id"], loan["library"]["id"], loan["status"])

        # Update loan -> mark as returned
        upd = LoanUpdate(status=LoanStatus.RETURNED)
        loan2 = await update_loan(session=session, loan_id=loan["id"], data=upd, payload=payload)
        print("Updated loan status:", loan2["id"], loan2["status"], loan2["return_date"])

        # Delete loan (should be allowed because returned and fine 0)
        res = await delete_loan(session=session, loan_id=loan["id"], payload=payload)
        print("Delete result:", res)

if __name__ == "__main__":
    asyncio.run(main())
