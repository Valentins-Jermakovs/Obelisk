import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, 'src')

import pytest
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

# use a unique SQLite test database path per run to avoid conflicts
test_db_path = Path('/tmp') / f'obelisk_test_{uuid.uuid4().hex}.db'
os.environ['DATABASE_URL'] = f'sqlite+aiosqlite:///{test_db_path}'

from config.database import AsyncSessionLocal, engine
from sqlmodel import SQLModel

from models import (
    DimAuthor, DimGenre, DimLanguage, DimLibrary, DimShelf,
    DimLibrarian, LibrarianLibrary, DimBook, DimBookCopy, BookPosition,
    DimPublisher
)

from schemas.book import BookCreate, BookCopyCreate, BookPositionCreate, BookUpdate
from services.book_service import (
    create_book, search_books, get_book, update_book, delete_book
)
from services.library_service import delete_library

@pytest.mark.asyncio
async def test_book_supports_publisher_and_pages_and_search_by_publisher():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        author = DimAuthor(name='Publisher Author')
        genre = DimGenre(name='Publisher Genre')
        language = DimLanguage(code='en', name='English')
        library = DimLibrary(name='Publisher Library', city='City', address='Addr')
        publisher = DimPublisher(name='Example Publisher', country='US')

        session.add_all([author, genre, language, library, publisher])
        await session.commit()
        await session.refresh(author)
        await session.refresh(genre)
        await session.refresh(language)
        await session.refresh(library)
        await session.refresh(publisher)

        shelf = DimShelf(library_id=library.id, code='P-01')
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        book = await create_book(
            session,
            BookCreate(
                title='Publisher Search Book',
                isbn='ISBN-PUBLISHER-1',
                annotation='Publisher search test',
                publication_year=2024,
                pages=320,
                publisher_id=publisher.id,
                authors=[author.id],
                genres=[genre.id],
                languages=[language.id],
                images=[],
                copies=[]
            )
        )

        assert book.publisher_id == publisher.id
        assert book.pages == 320

        searched = await search_books(session, query='Example Publisher', limit=10, offset=0)
        assert searched['total'] >= 1
        assert any(item['title'] == 'Publisher Search Book' for item in searched['items'])

        updated = await update_book(
            session,
            book.id,
            BookUpdate(pages=400)
        )
        assert updated.pages == 400


@pytest.mark.asyncio
async def test_book_crud_flow():
    # initialize DB on the same engine used by AsyncSessionLocal
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
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
        assert bk['copies'][0]['shelf'] is not None
        assert bk['copies'][0]['position'] is not None

        # update
        from schemas.book import BookUpdate
        upd = BookUpdate(title='Updated Title')
        book2 = await update_book(session, book.id, upd)
        assert book2.title == 'Updated Title'

        # delete (force)
        delr = await delete_book(session, book.id, force=True)
        assert delr.get('status') == 'deleted'


@pytest.mark.asyncio
async def test_create_book_fails_when_copy_position_is_already_occupied():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        author = DimAuthor(name='Position Author')
        genre = DimGenre(name='Position Genre')
        language = DimLanguage(code='pt', name='Portuguese')
        library = DimLibrary(name='Position Library', city='CityP', address='AddrP')

        session.add_all([author, genre, language, library])
        await session.commit()
        await session.refresh(author)
        await session.refresh(genre)
        await session.refresh(language)
        await session.refresh(library)

        shelf = DimShelf(library_id=library.id, code='POS-1')
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        existing_book = DimBook(title='Existing', isbn='ISBN-EXIST', publication_year=2020)
        session.add(existing_book)
        await session.commit()
        await session.refresh(existing_book)

        existing_copy = DimBookCopy(book_id=existing_book.id, inventory_code='INV-EXIST', condition='good')
        session.add(existing_copy)
        await session.flush()
        session.add(BookPosition(book_copy_id=existing_copy.id, shelf_id=shelf.id, row=1, column=2, depth=3))
        await session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await create_book(
                session,
                BookCreate(
                    title='New Book',
                    isbn='ISBN-NEW-POS',
                    annotation='Test',
                    publication_year=2021,
                    authors=[author.id],
                    genres=[genre.id],
                    languages=[language.id],
                    copies=[BookCopyCreate(
                        inventory_code='INV-NEW',
                        condition='good',
                        position=BookPositionCreate(shelf_id=shelf.id, row=1, column=2, depth=3)
                    )]
                )
            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == 'Позиция уже занята'


@pytest.mark.asyncio
async def test_create_book_fails_when_multiple_copies_share_the_same_position():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        author = DimAuthor(name='Shared Position Author')
        genre = DimGenre(name='Shared Position Genre')
        language = DimLanguage(code='es', name='Spanish')
        library = DimLibrary(name='Shared Position Library', city='CityS', address='AddrS')

        session.add_all([author, genre, language, library])
        await session.commit()
        await session.refresh(author)
        await session.refresh(genre)
        await session.refresh(language)
        await session.refresh(library)

        shelf = DimShelf(library_id=library.id, code='SP-1')
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        with pytest.raises(HTTPException) as exc_info:
            await create_book(
                session,
                BookCreate(
                    title='Shared Position Book',
                    isbn='ISBN-SHARED-POS',
                    annotation='Test',
                    publication_year=2021,
                    authors=[author.id],
                    genres=[genre.id],
                    languages=[language.id],
                    copies=[
                        BookCopyCreate(
                            inventory_code='INV-A',
                            condition='good',
                            position=BookPositionCreate(shelf_id=shelf.id, row=1, column=2, depth=3)
                        ),
                        BookCopyCreate(
                            inventory_code='INV-B',
                            condition='good',
                            position=BookPositionCreate(shelf_id=shelf.id, row=1, column=2, depth=3)
                        )
                    ]
                )
            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == 'Позиция уже занята'


@pytest.mark.asyncio
async def test_deleting_library_also_removes_associated_books_and_copies():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        author = DimAuthor(name='Library Author Two')
        genre = DimGenre(name='Library Genre Two')
        language = DimLanguage(code='it', name='Italian')
        library = DimLibrary(name='Delete Me Library', city='CityD', address='AddrD')

        session.add_all([author, genre, language, library])
        await session.commit()
        await session.refresh(author)
        await session.refresh(genre)
        await session.refresh(language)
        await session.refresh(library)

        shelf = DimShelf(library_id=library.id, code='DEL-01')
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        book = await create_book(
            session,
            BookCreate(
                title='Library Book',
                isbn='ISBN-LIB-DELETE',
                annotation='Delete me with the library',
                publication_year=2025,
                authors=[author.id],
                genres=[genre.id],
                languages=[language.id],
                copies=[BookCopyCreate(
                    inventory_code='INV-LIB-DELETE',
                    condition='good',
                    position=BookPositionCreate(shelf_id=shelf.id)
                )]
            )
        )

        assert book.id is not None

        result = await delete_library(session, library.id, force=True)

        assert result.get('status') == 'deleted'

        remaining_book = await session.get(DimBook, book.id)
        remaining_copy = (await session.exec(
            select(DimBookCopy).where(DimBookCopy.inventory_code == 'INV-LIB-DELETE')
        )).first()
        assert remaining_book is None
        assert remaining_copy is None


@pytest.mark.asyncio
async def test_librarian_can_delete_book_in_assigned_library():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # create entities
        author = DimAuthor(name='Assigned Author')
        genre = DimGenre(name='Assigned Genre')
        language = DimLanguage(code='fr', name='French')
        library = DimLibrary(name='Assigned Library', city='CityX', address='AddrX')
        librarian = DimLibrarian(full_name='Librarian One', email='lib1@example.com')

        session.add_all([author, genre, language, library, librarian])
        await session.commit()
        await session.refresh(author)
        await session.refresh(genre)
        await session.refresh(language)
        await session.refresh(library)
        await session.refresh(librarian)

        shelf = DimShelf(library_id=library.id, code='S-01')
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        # assign librarian to the library
        session.add(LibrarianLibrary(librarian_id=librarian.id, library_id=library.id))
        await session.commit()

        book = await create_book(
            session,
            BookCreate(
                title='Assigned Book',
                isbn='ISBN-ASSIGNED',
                annotation='Assigned annotation',
                publication_year=2023,
                authors=[author.id],
                genres=[genre.id],
                languages=[language.id],
                copies=[BookCopyCreate(inventory_code='INV-ASSIGN', condition='good', position=BookPositionCreate(shelf_id=shelf.id))]
            ),
            payload={"roles": ["librarian"], "email": librarian.email}
        )

        assert book.id is not None

        result = await delete_book(
            session,
            book.id,
            force=True,
            payload={"roles": ["librarian"], "email": librarian.email}
        )

        assert result.get('status') == 'deleted'


@pytest.mark.asyncio
async def test_librarian_cannot_delete_book_in_unassigned_library():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        author = DimAuthor(name='Other Author')
        genre = DimGenre(name='Other Genre')
        language = DimLanguage(code='de', name='German')
        library = DimLibrary(name='Other Library', city='CityY', address='AddrY')
        other_library = DimLibrary(name='Unassigned Library', city='CityZ', address='AddrZ')
        librarian = DimLibrarian(full_name='Librarian Two', email='lib2@example.com')

        session.add_all([author, genre, language, library, other_library, librarian])
        await session.commit()
        await session.refresh(author)
        await session.refresh(genre)
        await session.refresh(language)
        await session.refresh(library)
        await session.refresh(other_library)
        await session.refresh(librarian)

        shelf = DimShelf(library_id=other_library.id, code='S-02')
        session.add(shelf)
        await session.commit()
        await session.refresh(shelf)

        book = await create_book(
            session,
            BookCreate(
                title='Unassigned Book',
                isbn='ISBN-UNASSIGNED',
                annotation='Unassigned annotation',
                publication_year=2024,
                authors=[author.id],
                genres=[genre.id],
                languages=[language.id],
                copies=[BookCopyCreate(inventory_code='INV-UNASSIGN', condition='fair', position=BookPositionCreate(shelf_id=shelf.id))]
            )
        )

        with pytest.raises(HTTPException) as exc_info:
            await delete_book(
                session,
                book.id,
                force=True,
                payload={"roles": ["librarian"], "email": librarian.email}
            )

        assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_inventory_code_allowed_in_different_libraries():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSessionLocal() as session:
        author = DimAuthor(name='Library Author')
        genre = DimGenre(name='Library Genre')
        language = DimLanguage(code='ru', name='Russian')
        library1 = DimLibrary(name='Library One', city='CityA', address='Address A')
        library2 = DimLibrary(name='Library Two', city='CityB', address='Address B')

        session.add_all([author, genre, language, library1, library2])
        await session.commit()
        await session.refresh(author)
        await session.refresh(genre)
        await session.refresh(language)
        await session.refresh(library1)
        await session.refresh(library2)

        shelf1 = DimShelf(library_id=library1.id, code='A1')
        shelf2 = DimShelf(library_id=library2.id, code='B1')
        session.add_all([shelf1, shelf2])
        await session.commit()
        await session.refresh(shelf1)
        await session.refresh(shelf2)

        book1 = await create_book(session, BookCreate(
            title='Book A',
            isbn='ISBN-A-1',
            annotation='A',
            publication_year=2021,
            authors=[author.id],
            genres=[genre.id],
            languages=[language.id],
            copies=[BookCopyCreate(inventory_code='INV-100', condition='good', position=BookPositionCreate(shelf_id=shelf1.id))]
        ))

        book2 = await create_book(session, BookCreate(
            title='Book B',
            isbn='ISBN-B-1',
            annotation='B',
            publication_year=2022,
            authors=[author.id],
            genres=[genre.id],
            languages=[language.id],
            copies=[BookCopyCreate(inventory_code='INV-100', condition='good', position=BookPositionCreate(shelf_id=shelf2.id))]
        ))

        assert book1.id is not None
        assert book2.id is not None
