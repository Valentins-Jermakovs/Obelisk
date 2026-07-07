import asyncio
import os
import sys
from pathlib import Path
from sqlmodel import SQLModel, create_engine

# Ensure project src is importable
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

import models  # noqa: F401
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
from services.loan.loan_service import create_loan, update_loan, delete_loan

DB_PATH = "/tmp/obelisk_test_pytest.db"
SYNC_URL = f"sqlite:///{DB_PATH}"
ASYNC_URL = f"sqlite+aiosqlite:///{DB_PATH}"


async def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    sync_engine = create_engine(SYNC_URL)
    SQLModel.metadata.create_all(sync_engine)

    async_engine = create_async_engine(ASYNC_URL, echo=False)
    AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    return AsyncSessionLocal


def test_loans_crud():
    async def _run():
        AsyncSessionLocal = await setup_db()
        async with AsyncSessionLocal() as session:
            lib = DimLibrary(name="TestLib", city="City", address="Addr")
            session.add(lib)
            await session.commit()
            await session.refresh(lib)

            shelf = DimShelf(library_id=lib.id, code="A-1")
            session.add(shelf)
            await session.commit()
            await session.refresh(shelf)

            reader = DimReader(full_name="R", email="r@example.com")
            session.add(reader)
            await session.commit()
            await session.refresh(reader)

            book = DimBook(title="T", isbn="I-1", publication_year=2020)
            session.add(book)
            await session.commit()
            await session.refresh(book)

            copy = DimBookCopy(book_id=book.id, inventory_code="INV1")
            session.add(copy)
            await session.commit()
            await session.refresh(copy)

            pos = BookPosition(book_copy_id=copy.id, shelf_id=shelf.id)
            session.add(pos)
            await session.commit()

            libn = DimLibrarian(full_name="L", email="l@example.com")
            session.add(libn)
            await session.commit()
            await session.refresh(libn)

            assign = LibrarianLibrary(librarian_id=libn.id, library_id=lib.id)
            session.add(assign)
            await session.commit()

            payload = {"roles": ["librarian"], "email": "l@example.com"}

            data = LoanCreate(book_copy_id=copy.id, reader_id=reader.id, library_id=lib.id)
            created = await create_loan(session=session, data=data, payload=payload)
            assert isinstance(created, dict)
            assert created["status"] == LoanStatus.ACTIVE

            upd = LoanUpdate(status=LoanStatus.RETURNED)
            updated = await update_loan(session=session, loan_id=created["id"], data=upd, payload=payload)
            assert updated["status"] == LoanStatus.RETURNED

            res = await delete_loan(session=session, loan_id=created["id"], payload=payload)
            assert res["status"] == "deleted"

    asyncio.run(_run())


if __name__ == '__main__':
    asyncio.run(test_loans_crud())
