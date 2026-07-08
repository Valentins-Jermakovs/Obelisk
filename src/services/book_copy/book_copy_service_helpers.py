# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import (
    BookPosition,
    DimShelf,
    FactLoan,
    DimLibrarian,
    LibrarianLibrary
)

# ===================================================
#            Helper functions for book_copy service
# ===================================================

async def _get_copy_library_id(
    session: AsyncSession,
    copy_id: int
) -> int:

    # Get book position data
    stmt = (
        select(DimShelf.library_id)
        .join(
            BookPosition,
            BookPosition.shelf_id == DimShelf.id
        )
        .where(
            BookPosition.book_copy_id == copy_id
        )
    )

    # Get library id from book position data
    library_id = (
        await session.exec(stmt)
    ).first()

    if library_id is None:
        raise HTTPException(
            status_code=404,
            detail="Book position not found"
        )

    return library_id


async def _get_last_loan(
    session: AsyncSession,
    copy_id: int
):
    # Get last loan data
    stmt = (
        select(FactLoan)
        .where(
            FactLoan.book_copy_id == copy_id
        )
        .order_by(
            FactLoan.borrowed_at.desc()
        )
    )

    return (
        await session.exec(stmt)
    ).first()


# Get librarian email from access token payload
async def _get_librarian_from_payload(
    session: AsyncSession,
    payload: dict
) -> DimLibrarian | None:
    # If token is invalid or does not contain librarian role
    if "librarian" not in payload.get("roles", []):
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload or missing librarian role"
        )

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


# Check librarian access to library
async def _validate_librarian_access_to_library(
    session: AsyncSession,
    payload: dict,
    library_id: int
):
    # Admin can access any library
    if "admin" in payload.get("roles", []):
        return

    # Get librarian
    librarian = await _get_librarian_from_payload(
        session,
        payload
    )

    # Check assignment
    assignment = (
        await session.exec(
            select(LibrarianLibrary).where(
                LibrarianLibrary.librarian_id == librarian.id,
                LibrarianLibrary.library_id == library_id
            )
        )
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this library"
        )
    

# Get accessible library IDs
async def _get_accessible_library_ids(
    session: AsyncSession,
    payload: dict
):

    # Get librarian ID
    librarian = await _get_librarian_from_payload(
        session,
        payload
    )

    # Get accessible library IDs
    rows = await session.exec(
        select(LibrarianLibrary.library_id)
        .where(
            LibrarianLibrary.librarian_id == librarian.id
        )
    )


    return rows.all()