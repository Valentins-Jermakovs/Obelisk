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
    DimShelf,
    DimLibrarian,
    LibrarianLibrary
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


async def _get_librarian_from_payload(
    session: AsyncSession,
    payload: dict
) -> DimLibrarian | None:
    if "librarian" not in payload.get("roles", []):
        return None

    email = payload.get("email")

    if not email:
        raise HTTPException(401, "Invalid token payload")

    librarian = (await session.exec(
        select(DimLibrarian).where(DimLibrarian.email == email)
    )).first()

    if not librarian:
        raise HTTPException(404, "Librarian not found")

    return librarian


async def _validate_librarian_access_to_book(
    session: AsyncSession,
    payload: dict,
    book_id: int
):
    if "admin" in payload.get("roles", []):
        return

    librarian = await _get_librarian_from_payload(session, payload)

    library_stmt = select(DimShelf.library_id).join(
        BookPosition,
        BookPosition.shelf_id == DimShelf.id
    ).join(
        DimBookCopy,
        DimBookCopy.id == BookPosition.book_copy_id
    ).where(
        DimBookCopy.book_id == book_id
    ).distinct()

    library_rows = (await session.exec(library_stmt)).all()
    library_ids = [row[0] if isinstance(row, tuple) else row for row in library_rows]

    if not library_ids:
        return

    assigned_rows = (await session.exec(
        select(LibrarianLibrary.library_id).where(
            LibrarianLibrary.librarian_id == librarian.id,
            LibrarianLibrary.library_id.in_(library_ids)
        )
    )).all()
    assigned_ids = [row[0] if isinstance(row, tuple) else row for row in assigned_rows]

    if set(assigned_ids) != set(library_ids):
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to all libraries containing this book"
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


async def _validate_copies(
    session: AsyncSession,
    copies: list,
    payload: dict | None = None
):
    if not copies:
        return

    librarian = None
    if payload and "admin" not in payload.get("roles", []):
        librarian = await _get_librarian_from_payload(session, payload)

    for c in copies:
        shelf = await session.get(DimShelf, c.position.shelf_id)

        if not shelf:
            raise HTTPException(
                status_code=404,
                detail=f"Shelf {c.position.shelf_id} not found"
            )

        if librarian:
            access = (await session.exec(
                select(LibrarianLibrary).where(
                    LibrarianLibrary.librarian_id == librarian.id,
                    LibrarianLibrary.library_id == shelf.library_id
                )
            )).first()

            if not access:
                raise HTTPException(
                    status_code=403,
                    detail=f"You are not assigned to library {shelf.library_id}"
                )

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


async def _create_copies(
    session: AsyncSession,
    book_id: int,
    copies: list,
    payload: dict | None = None
):
    if not copies:
        return

    await _validate_copies(session, copies, payload)

    librarian = None
    if payload and "admin" not in payload.get("roles", []):
        librarian = await _get_librarian_from_payload(session, payload)

    for c in copies:

        # check shelf first
        shelf = await session.get(DimShelf, c.position.shelf_id)

        if not shelf:
            raise HTTPException(
                status_code=404,
                detail=f"Shelf {c.position.shelf_id} not found"
            )

        if librarian:
            access = (await session.exec(
                select(LibrarianLibrary).where(
                    LibrarianLibrary.librarian_id == librarian.id,
                    LibrarianLibrary.library_id == shelf.library_id
                )
            )).first()

            if not access:
                raise HTTPException(
                    status_code=403,
                    detail=f"You are not assigned to library with shelf [id: {shelf.library_id}] [code: {shelf.code}]"
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