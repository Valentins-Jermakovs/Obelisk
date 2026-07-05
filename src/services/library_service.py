

# ====================================================
#                       imports
# ====================================================
# Libraries:
from sqlmodel import select, or_
from sqlalchemy import func
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import DimLibrary, DimShelf, FactLoan, LibrarianLibrary
# Schemas:
from schemas.library import LibraryCreate, LibraryUpdate
# ====================================================


# ===================================================
#                       functions
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

    data = normalize_library(data_in.model_dump())

    # unique check
    stmt = select(DimLibrary).where(
        DimLibrary.name == data["name"]
    )

    if (await session.exec(stmt)).first():
        raise HTTPException(
            status_code=409, 
            detail="Library already exists"
        )

    library = DimLibrary(**data)

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
    stmt = select(DimLibrary)

    # optional filtering
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

    # total count (with or without filter)
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.exec(total_stmt)).one()

    # pagination
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

    library = await session.get(DimLibrary, library_id)

    if not library:
        raise HTTPException(
            status_code=404, 
            detail="Library not found"
        )

    return format_library(library)


# Update library
async def update_library(
    session: AsyncSession, 
    library_id: int, 
    data_in: LibraryUpdate
):

    library = await session.get(DimLibrary, library_id)

    if not library:
        raise HTTPException(404, "Library not found")

    data = normalize_library(data_in.model_dump(exclude_unset=True))

    # unique name check
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

    for k, v in data.items():
        setattr(library, k, v)

    await session.commit()
    await session.refresh(library)

    return format_library(library)


# Delete library
async def delete_library(
    session: AsyncSession,
    library_id: int,
    force: bool = False
):

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


    # IF RELATIONS EXIST -> BLOCK OR WARN
    has_relations = bool(shelves or loans or links)

    if has_relations and not force:
        return {
            "warning": "Library has related data",
            "details": {
                "shelves": len(shelves),
                "loans": len(loans),
                "librarian_links": len(links)
            },
            "message": "Pass force=True to delete anyway"
        }


    # FORCE DELETE LOGIC
    if force:
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
        "forced": force
    }