# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import (
    DimBook,
    BookAuthor,
    BookGenre,
    BookLanguage,
    BookImage,
    DimBookCopy,
    BookPosition,
    DimShelf
)
# ===================================================


# ===================================================
#                       functions
# ===================================================

async def _check_isbn_unique(session: AsyncSession, isbn: str):
    existing = (
        await session.exec(
            select(DimBook).where(DimBook.isbn == isbn)
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Book with this ISBN already exists"
        )
    
async def _validate_existing_ids(
    session: AsyncSession,
    model,
    ids: list[int],
    entity_name: str
):
    if not ids:
        return

    stmt = select(model).where(model.id.in_(ids))
    result = await session.exec(stmt)
    found = result.all()

    found_ids = {item.id for item in found}
    missing = set(ids) - found_ids

    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"{entity_name} not found: {list(missing)}"
        )
    

async def _create_book(session: AsyncSession, data):
    book = DimBook(
        title=data.title.strip(),
        isbn=data.isbn.strip(),
        annotation=data.annotation,
        publication_year=data.publication_year
    )

    session.add(book)
    await session.flush()

    return book


async def _link_authors(session: AsyncSession, book_id: int, author_ids: list[int]):
    if not author_ids:
        return

    for aid in set(author_ids):
        session.add(BookAuthor(
            book_id=book_id,
            author_id=aid
        ))


async def _link_genres(session: AsyncSession, book_id: int, genre_ids: list[int]):
    if not genre_ids:
        return

    for gid in set(genre_ids):
        session.add(BookGenre(
            book_id=book_id,
            genre_id=gid
        ))


async def _link_languages(session: AsyncSession, book_id: int, language_ids: list[int]):
    if not language_ids:
        return

    for lid in set(language_ids):
        session.add(BookLanguage(
            book_id=book_id,
            language_id=lid
        ))


async def _create_images(session: AsyncSession, book_id: int, images: list):
    if not images:
        return

    for img in images:
        session.add(BookImage(
            book_id=book_id,
            file_path=img.file_path,
            image_type=img.image_type,
            display_order=img.display_order
        ))


async def _create_copies(session: AsyncSession, book_id: int, copies: list):
    if not copies:
        return

    for c in copies:

        # check shelf first
        shelf = await session.get(DimShelf, c.position.shelf_id)

        if not shelf:
            raise HTTPException(
                status_code=404,
                detail=f"Shelf {c.position.shelf_id} not found"
            )

        # check inventory code uniqueness within the same library
        existing_copy = (await session.exec(
            select(DimBookCopy)
            .join(BookPosition, BookPosition.book_copy_id == DimBookCopy.id)
            .where(
                DimBookCopy.inventory_code == c.inventory_code.strip(),
                BookPosition.shelf_id.in_(
                    select(DimShelf.id).where(DimShelf.library_id == shelf.library_id)
                )
            )
        )).first()

        if existing_copy:
            raise HTTPException(
                status_code=409,
                detail=f"Inventory code '{c.inventory_code}' already exists in library {shelf.library_id}"
            )

        # create copy
        copy = DimBookCopy(
            book_id=book_id,
            inventory_code=c.inventory_code.strip(),
            condition=c.condition
        )

        session.add(copy)
        await session.flush()

        # position
        session.add(BookPosition(
            book_copy_id=copy.id,
            shelf_id=c.position.shelf_id,
            row=c.position.row,
            column=c.position.column,
            depth=c.position.depth
        ))