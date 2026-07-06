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
#            Helper functions for book service
# ===================================================

# Check if book with given ISBN exists
async def _check_isbn_unique(
    session: AsyncSession, 
    isbn: str
):
    # Try to find existing book in database
    existing = (
        await session.exec(
            select(DimBook).where(DimBook.isbn == isbn)
        )
    ).first()

    # If book with given ISBN exists, raise Error message
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Book with this ISBN already exists"
        )


# Get librarian email from access token payload
async def _get_librarian_from_payload(
    session: AsyncSession,
    payload: dict
) -> DimLibrarian | None:
    
    # If token is invalid or does not contain librarian role
    if "librarian" not in payload.get("roles", []):
        return None

    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token payload"
        )

    # Try to get librarian from database
    librarian = (await session.exec(
        select(DimLibrarian).where(DimLibrarian.email == email)
    )).first()

    # Raise error if librarian not found
    if not librarian:
        raise HTTPException(
            status_code=404,
            detail="Librarian not found"
        )

    return librarian


# Check if librarian has access to book
async def _validate_librarian_access_to_book(
    session: AsyncSession,
    payload: dict,
    book_id: int
):
    
    # If token contain admin role, skip validation
    if "admin" in payload.get("roles", []):
        return

    # Get librarian data (email) and check it exists
    librarian = await _get_librarian_from_payload(session, payload)

    # Get book data
    library_stmt = select(DimShelf.library_id).join(
        BookPosition,
        BookPosition.shelf_id == DimShelf.id
    ).join(
        DimBookCopy,
        DimBookCopy.id == BookPosition.book_copy_id
    ).where(
        DimBookCopy.book_id == book_id
    ).distinct()

    # Get library ids from book
    library_rows = (await session.exec(library_stmt)).all()
    library_ids = [row[0] if isinstance(row, tuple) else row for row in library_rows]

    # If no library ids exist, skip validation
    if not library_ids:
        return

    # Get librarian library ids from library
    assigned_rows = (await session.exec(
        select(LibrarianLibrary.library_id).where(
            LibrarianLibrary.librarian_id == librarian.id,
            LibrarianLibrary.library_id.in_(library_ids)
        )
    )).all()

    # If no assigned library ids exist, skip validation
    assigned_ids = [row[0] if isinstance(row, tuple) else row for row in assigned_rows]

    # If the librarian is not assigned to all libraries containing
    if set(assigned_ids) != set(library_ids):
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to all libraries containing this book"
        )


# This function validate ID's
async def _validate_existing_ids(
    session: AsyncSession,
    model,
    ids: list[int],
    entity_name: str
):
    # If no IDs exist, skip validation
    if not ids:
        return

    # If the IDs exist, validate them
    stmt = select(model).where(model.id.in_(ids))
    result = await session.exec(stmt)
    found = result.all()

    # If the IDs do not exist, raise an error
    found_ids = {item.id for item in found}
    missing = set(ids) - found_ids

    if missing:
        raise HTTPException(
            status_code=404,
            detail=f"{entity_name} not found: {list(missing)}"
        )
    

# This function create a new book
async def _create_book(
    session: AsyncSession, 
    data
):
    book = DimBook(
        title=data.title.strip(),
        isbn=data.isbn.strip(),
        annotation=data.annotation,
        publication_year=data.publication_year
    )

    # Add the new book to the database
    session.add(book)
    # Flush the changes to the database
    await session.flush()

    return book


# This function link authors to a book
async def _link_authors(
    session: AsyncSession, 
    book_id: int, 
    author_ids: list[int]
):
    # If there are no authors to link, do nothing
    if not author_ids:
        return

    # Link the authors to the book
    for aid in set(author_ids):
        session.add(BookAuthor(
            book_id=book_id,
            author_id=aid
        ))


# This function link genres to a book
async def _link_genres(
    session: AsyncSession, 
    book_id: int, 
    genre_ids: list[int]
):
    # If there are no genres to link, do nothing
    if not genre_ids:
        return

    # Link the genres to the book
    for gid in set(genre_ids):
        session.add(BookGenre(
            book_id=book_id,
            genre_id=gid
        ))


# This function link languages to a book
async def _link_languages(
    session: AsyncSession, 
    book_id: int, 
    language_ids: list[int]
):
    # If there are no languages to link, do nothing
    if not language_ids:
        return

    # Link the languages to the book
    for lid in set(language_ids):
        session.add(BookLanguage(
            book_id=book_id,
            language_id=lid
        ))


# This function link images to a book
async def _create_images(
    session: AsyncSession, 
    book_id: int, 
    images: list
):
    # If there are no images to link, do nothing
    if not images:
        return

    # Link the images to the book
    for img in images:
        session.add(BookImage(
            book_id=book_id,
            file_path=img.file_path,
            image_type=img.image_type,
            display_order=img.display_order
        ))


# This function validate the copies of a book
async def _validate_copies(
    session: AsyncSession,
    copies: list,
    payload: dict | None = None
):
    # If there are no copies to validate, do nothing
    if not copies:
        return

    # Extract the librarian data from the payload
    librarian = None
    if payload and "admin" not in payload.get("roles", []):
        librarian = await _get_librarian_from_payload(session, payload)

    # Validate the copies of the book
    for c in copies:
        # If the copy is already in the database, do nothing
        shelf = await session.get(DimShelf, c.position.shelf_id)

        # If the copy is not in the database, raise an Error
        if not shelf:
            raise HTTPException(
                status_code=404,
                detail=f"Shelf {c.position.shelf_id} not found"
            )

        # Check librarian access to library
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

        # Try to find an existing copy with the same inventory code and position
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

        # If an existing copy is found, raise a 409 Conflict error
        if existing_copy:
            raise HTTPException(
                status_code=409,
                detail=f"Inventory code '{c.inventory_code}' already exists in library shelf ID: {shelf.library_id}"
            )


# Function that creates a copy of the book with the given inventory code and position. 
# It also validates that the inventory
async def _create_copies(
    session: AsyncSession,
    book_id: int,
    copies: list,
    payload: dict | None = None
):
    # If no copies are provided, return immediately
    if not copies:
        return

    # Validate the copies
    await _validate_copies(session, copies, payload)

    # Get librarian data (email) from access token payload
    librarian = None
    if payload and "admin" not in payload.get("roles", []):
        librarian = await _get_librarian_from_payload(session, payload)

    for c in copies:

        # Check shelf first
        shelf = await session.get(DimShelf, c.position.shelf_id)
        # Raise an Error, if shelf not exists
        if not shelf:
            raise HTTPException(
                status_code=404,
                detail=f"Shelf {c.position.shelf_id} not found"
            )

        # Check librarian access to library
        if librarian:
            access = (await session.exec(
                select(LibrarianLibrary).where(
                    LibrarianLibrary.librarian_id == librarian.id,
                    LibrarianLibrary.library_id == shelf.library_id
                )
            )).first()
            # Raise an Error if librarian not assigned to library
            if not access:
                raise HTTPException(
                    status_code=403,
                    detail=f"You are not assigned to library with shelf [id: {shelf.library_id}] [code: {shelf.code}]"
                )

        # Check inventory code uniqueness within the same library
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

        # Raise an error if inventory code already exists in the same library
        if existing_copy:
            raise HTTPException(
                status_code=409,
                detail=f"Inventory code '{c.inventory_code}' already exists in library {shelf.library_id}"
            )

        # Create copy
        copy = DimBookCopy(
            book_id=book_id,
            inventory_code=c.inventory_code.strip(),
            condition=c.condition
        )

        # Add to session
        session.add(copy)
        await session.flush()

        # Write book position
        session.add(BookPosition(
            book_copy_id=copy.id,
            shelf_id=c.position.shelf_id,
            row=c.position.row,
            column=c.position.column,
            depth=c.position.depth
        ))