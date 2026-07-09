import os
import sys
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import models  # noqa: F401
from models import DimBook, DimBookCopy, DimLibrarian, DimLibrary, DimShelf, LibrarianLibrary
from schemas.book_copy import BookCopyCreate, BookCopyUpdate
from services.book_copy_service import create_book_copy, update_book_copy

DB_PATH = "/tmp/obelisk_book_copy_pytest.db"
SYNC_URL = f"sqlite:///{DB_PATH}"
ASYNC_URL = f"sqlite+aiosqlite:///{DB_PATH}"


@pytest.fixture
def async_session_local():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    sync_engine = create_engine(SYNC_URL)
    SQLModel.metadata.create_all(sync_engine)

    async_engine = create_async_engine(ASYNC_URL, echo=False)
    session_local = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    return session_local


@pytest.mark.asyncio
async def test_update_book_copy_with_none_inventory_code_does_not_fail(async_session_local):
    async with async_session_local() as session:
        library = DimLibrary(name="Lib", city="City", address="Addr")
        session.add(library)
        await session.commit()
        await session.refresh(library)

        shelf = DimShelf(library_id=library.id, code="S-1")
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        book = DimBook(title="Sample", isbn="ISBN-1", publication_year=2020)
        session.add(book)
        await session.commit()
        await session.refresh(book)

        librarian = DimLibrarian(full_name="Librarian", email="lib@example.com")
        session.add(librarian)
        await session.commit()
        await session.refresh(librarian)

        session.add(LibrarianLibrary(librarian_id=librarian.id, library_id=library.id))
        await session.commit()

        payload = {"roles": ["librarian"], "email": "lib@example.com"}

        created = await create_book_copy(
            session=session,
            data=BookCopyCreate(
                book_id=book.id,
                library_id=library.id,
                shelf_id=shelf.id,
                inventory_code="INV-1",
            ),
            payload=payload,
        )

        updated = await update_book_copy(
            session=session,
            copy_id=created.id,
            data=BookCopyUpdate(inventory_code=None, row=7),
            payload=payload,
        )

        assert updated.inventory_code == "INV-1"
        assert updated.id == created.id
