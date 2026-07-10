# ====================================================
#                       imports
# ====================================================
# Libraries:
from sqlmodel import select, or_, func
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import (
    DimLibrary,
    DimShelf,
    FactLoan,
    LibrarianLibrary,
    DimBook,
    DimBookCopy,
    BookPosition,
    BookAuthor,
    BookGenre,
    BookLanguage,
    BookImage
)
# Schemas:
from schemas.library import LibraryCreate, LibraryUpdate



# ===================================================
#      Service code - create, update, get, delete
# ===================================================

# Normalize library data
def normalize_library(data: dict) -> dict:

    if "name" in data and data["name"]:
        data["name"] = data["name"].strip().lower()

    if "city" in data and data["city"]:
        data["city"] = data["city"].strip().lower()

    if "address" in data and data["address"]:
        data["address"] = data["address"].strip()

    return data

# Format library data for display in UI
def format_library(lib: DimLibrary) -> DimLibrary:
    
    return DimLibrary(
        id=lib.id,
        name=lib.name.title(),
        city=lib.city.title(),
        address=lib.address
    )


# Create library
async def create_library(
    session: AsyncSession, 
    data_in: LibraryCreate
):
    # Normalize the data for storage in the database
    data = normalize_library(data_in.model_dump())

    # Unique check
    stmt = select(DimLibrary).where(
        DimLibrary.name == data["name"]
    )

    # Check for a duplicate library
    if (await session.exec(stmt)).first():
        raise HTTPException(
            status_code=409, 
            detail="Library already exists"
        )

    # Create a new library instance
    library = DimLibrary(**data)

    # Add the library to the session and commit it
    session.add(library)
    await session.commit()
    await session.refresh(library)

    return format_library(library)


# Search library by city/name/address
async def search_libraries(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # Create a query statement
    stmt = select(DimLibrary)

    # Optional filtering - name/city/address
    if query:
        q = query.strip().lower()

        if q:
            stmt = stmt.where(
                or_(
                    DimLibrary.name.ilike(f"%{q}%"),
                    DimLibrary.city.ilike(f"%{q}%"),
                    DimLibrary.address.ilike(f"%{q}%")
                )
            )

    # Total count (with or without filter)
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.exec(total_stmt)).one()

    # Pagination
    stmt = stmt.offset(offset).limit(limit)
    result = await session.exec(stmt)
    libraries = result.all()

    return {
        "items": [format_library(l) for l in libraries],
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(libraries)
    }


# Get library by ID
async def get_library(
    session: AsyncSession, 
    library_id: int
):
    # Get the library by ID
    library = await session.get(DimLibrary, library_id)

    if not library:
        raise HTTPException(
            status_code=404, 
            detail="Library not found"
        )

    return format_library(library)


# Update library by ID
async def update_library(
    session: AsyncSession, 
    library_id: int, 
    data_in: LibraryUpdate
):
    # Get the library by ID
    library = await session.get(DimLibrary, library_id)

    if not library:
        raise HTTPException(404, "Library not found")

    # Normalize the data
    data = normalize_library(data_in.model_dump(exclude_unset=True))

    # Unique name check
    if "name" in data:
        stmt = select(DimLibrary).where(
            DimLibrary.name == data["name"],
            DimLibrary.id != library_id
        )

        if (await session.exec(stmt)).first():
            raise HTTPException(
                status_code=409, 
                detail="Library name already exists"
            )

    # Update the library attributes
    for k, v in data.items():
        setattr(library, k, v)

    # Commit the changes
    await session.commit()
    await session.refresh(library)

    return format_library(library)


# Delete library by ID
async def delete_library(
    session: AsyncSession,
    library_id: int,
    force: bool = False
):
    # Check if the library exists
    library = await session.get(DimLibrary, library_id)

    if not library:
        raise HTTPException(
            status_code=404, 
            detail="Library not found"
        )


    # CHECK RELATIONS
    shelves = (await session.exec(
        select(DimShelf).where(DimShelf.library_id == library_id)
    )).all()

    loans = (await session.exec(
        select(FactLoan).where(FactLoan.library_id == library_id)
    )).all()

    links = (await session.exec(
        select(LibrarianLibrary).where(LibrarianLibrary.library_id == library_id)
    )).all()

    related_books = (await session.exec(
        select(DimBook)
        .join(DimBookCopy, DimBookCopy.book_id == DimBook.id)
        .join(BookPosition, BookPosition.book_copy_id == DimBookCopy.id)
        .join(DimShelf, BookPosition.shelf_id == DimShelf.id)
        .where(DimShelf.library_id == library_id)
        .distinct()
    )).all()

    related_copies = (await session.exec(
        select(DimBookCopy)
        .join(BookPosition, BookPosition.book_copy_id == DimBookCopy.id)
        .join(DimShelf, BookPosition.shelf_id == DimShelf.id)
        .where(DimShelf.library_id == library_id)
        .distinct()
    )).all()


    # IF RELATIONS EXIST -> BLOCK OR WARN
    has_relations = bool(shelves or loans or links or related_books or related_copies)

    if has_relations and not force:
        return {
            "warning": "Library has related data",
            "details": {
                "shelves": len(shelves),
                "loans": len(loans),
                "librarian_links": len(links),
                "books": len(related_books),
                "copies": len(related_copies)
            },
            "message": "Pass force=True to delete anyway"
        }


    # FORCE DELETE LOGIC
    if force:
        for book in related_books:
            copies = (await session.exec(
                select(DimBookCopy).where(DimBookCopy.book_id == book.id)
            )).all()
            copy_ids = [copy.id for copy in copies if copy.id is not None]

            if copy_ids:
                await session.exec(
                    BookPosition.__table__.delete().where(
                        BookPosition.book_copy_id.in_(copy_ids)
                    )
                )

                await session.exec(
                    FactLoan.__table__.delete().where(
                        FactLoan.book_copy_id.in_(copy_ids)
                    )
                )

                await session.exec(
                    DimBookCopy.__table__.delete().where(
                        DimBookCopy.id.in_(copy_ids)
                    )
                )

            await session.exec(
                BookAuthor.__table__.delete().where(BookAuthor.book_id == book.id)
            )
            await session.exec(
                BookGenre.__table__.delete().where(BookGenre.book_id == book.id)
            )
            await session.exec(
                BookLanguage.__table__.delete().where(BookLanguage.book_id == book.id)
            )
            await session.exec(
                BookImage.__table__.delete().where(BookImage.book_id == book.id)
            )

            await session.delete(book)

        for s in shelves:
            await session.delete(s)

        for l in links:
            await session.delete(l)

        for loan in loans:
            await session.delete(loan)

    # DELETE LIBRARY
    await session.delete(library)
    await session.commit()

    return {
        "status": "deleted",
        "forced": force,
        "deleted_books": len(related_books),
        "deleted_copies": len(related_copies)
    }