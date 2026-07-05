# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException, Depends
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func
# Models:
from models import (
    DimShelf, 
    DimLibrary, 
    LibrarianLibrary, 
    DimLibrarian, 
    BookPosition
)
# Utils:
from utils.token_utils import validate_token
# =====================================================


# ===================================================
#                       functions
# ===================================================


# Helper function: Get current librarian
async def get_current_librarian(
    session: AsyncSession,
    payload: dict
) -> DimLibrarian:
    email = payload.get("email")

    if not email:
        raise HTTPException(401, "Invalid token payload")

    librarian = (await session.exec(
        select(DimLibrarian).where(DimLibrarian.email == email)
    )).first()

    if not librarian:
        raise HTTPException(404, "Librarian not found")

    return librarian


# Helper function: Check library access
async def check_library_access(
    session: AsyncSession,
    librarian_id: int,
    library_id: int
):
    link = (await session.exec(
        select(LibrarianLibrary).where(
            LibrarianLibrary.librarian_id == librarian_id,
            LibrarianLibrary.library_id == library_id
        )
    )).first()

    if not link:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this library"
        )
    

# Search shelf
async def search_shelves(
    session: AsyncSession,
    library_id: int,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0,
):
    # base query
    base_stmt = select(DimShelf).where(
        DimShelf.library_id == library_id
    )

    # filtered query
    stmt = base_stmt

    if query:
        q = query.strip().lower()
        stmt = stmt.where(
            or_(
                DimShelf.code.ilike(f"%{q}%"),
                DimShelf.section.ilike(f"%{q}%")
            )
        )

    # pagination
    paginated_stmt = stmt.offset(offset).limit(limit)

    items = (await session.exec(paginated_stmt)).all()

    # total shelves in library (WITHOUT filter)
    total_stmt = select(func.count(DimShelf.id)).where(
        DimShelf.library_id == library_id
    )
    total = (await session.exec(total_stmt)).one()

    returned = len(items)

    return {
        "items": items,
        "total": total,
        "returned": returned,
        "library_total_shelves": total,
        "library_remaining": max(total - offset - returned, 0)
    }

# Create shelf
async def create_shelf(
    session: AsyncSession,
    library_id: int,
    code: str,
    section: str | None,
    payload: dict = Depends(validate_token)
):
    librarian = await get_current_librarian(session, payload)
    await check_library_access(session, librarian.id, library_id)

    shelf = DimShelf(
        library_id=library_id,
        code=code.strip().upper(),
        section=section.strip().title() if section else None
    )

    session.add(shelf)
    await session.commit()
    await session.refresh(shelf)

    return shelf


# Update shelf
async def update_shelf(
    session: AsyncSession,
    shelf_id: int,
    code: str | None = None,
    section: str | None = None,
    payload: dict = Depends(validate_token)
):
    shelf = await session.get(DimShelf, shelf_id)

    if not shelf:
        raise HTTPException(404, "Shelf not found")

    librarian = await get_current_librarian(session, payload)
    await check_library_access(session, librarian.id, shelf.library_id)

    if code is not None:
        shelf.code = code.strip().upper()

    if section is not None:
        shelf.section = section.strip().title()

    await session.commit()
    await session.refresh(shelf)

    return shelf


# Delete shelf
async def delete_shelf(
    session: AsyncSession,
    shelf_id: int,
    force: bool = False,
    payload: dict = Depends(validate_token)
):
    shelf = await session.get(DimShelf, shelf_id)

    if not shelf:
        raise HTTPException(404, "Shelf not found")

    librarian = await get_current_librarian(session, payload)
    await check_library_access(session, librarian.id, shelf.library_id)

    # check linked positions
    linked = (await session.exec(
        select(BookPosition).where(
            BookPosition.shelf_id == shelf_id
        )
    )).first()

    if linked and not force:
        raise HTTPException(
            status_code=409,
            detail="Shelf has books assigned. Use force=true to delete."
        )

    await session.delete(shelf)
    await session.commit()

    return {"status": "deleted"}