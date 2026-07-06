import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, 'src')

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

# use a unique SQLite test database path per run to avoid conflicts
test_db_path = Path('/tmp') / f'obelisk_test_{uuid.uuid4().hex}.db'
os.environ['DATABASE_URL'] = f'sqlite+aiosqlite:///{test_db_path}'

from config.database import AsyncSessionLocal, engine
from sqlmodel import SQLModel

from models import (
    DimAuthor, DimGenre, DimLanguage, DimLibrary, DimShelf
)

from schemas.book import BookCreate, BookCopyCreate, BookPositionCreate
from services.book.book_service import (
    create_book, search_books, get_book, update_book, delete_book
)

@pytest.mark.asyncio
async def test_book_crud_flow():
    # initialize DB on the same engine used by AsyncSessionLocal
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # create supporting entities
        author = DimAuthor(name='Test Author')
        genre = DimGenre(name='Test Genre')
        language = DimLanguage(code='en', name='English')
        library = DimLibrary(name='Test Library', city='Test City', address='Somewhere')
        # add shelf linked to library
        session.add(author)
        session.add(genre)
        session.add(language)
        session.add(library)
        await session.commit()
        await session.refresh(author)
        await session.refresh(genre)
        await session.refresh(language)
        await session.refresh(library)

        shelf = DimShelf(library_id=library.id, code='A-01')
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        # create book via service
        book_in = BookCreate(
            title='My Test Book',
            isbn='ISBN-12345',
            annotation='Test annotation',
            publication_year=2020,
            authors=[author.id],
            genres=[genre.id],
            languages=[language.id],
            images=[],
            copies=[BookCopyCreate(inventory_code='INV-1', condition='good', position=BookPositionCreate(shelf_id=shelf.id))]
        )

        book = await create_book(session, book_in)
        assert book.id is not None

        # search
        res = await search_books(session, query='My Test Book', limit=10, offset=0)
        assert res['total'] >= 1
        assert len(res['items']) >= 1
        item = res['items'][0]
        assert 'libraries' in item

        # get_book
        bk = await get_book(session, book.id)
        assert bk['id'] == book.id
        assert 'libraries' in bk

        # update
        from schemas.book import BookUpdate
        upd = BookUpdate(title='Updated Title')
        book2 = await update_book(session, book.id, upd)
        assert book2.title == 'Updated Title'

        # delete (force)
        delr = await delete_book(session, book.id, force=True)
        assert delr.get('status') == 'deleted'
