# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select, or_
from sqlmodel.ext.asyncio.session import AsyncSession
import re
# Models:
from models import DimLibrarian, DimLibrary, LibrarianLibrary
# Schemas:
from schemas.librarian import LibrarianCreate, LibrarianUpdate
# Utils:
from utils.formatters import format_full_name, format_library, format_librarian
# =====================================================


# ===================================================
#                       functions
# ===================================================


# Create librarian
async def create_librarian(
    session: AsyncSession, 
    data_in: LibrarianCreate
):
    email = data_in.email.strip().lower()

    email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        raise HTTPException(
            status_code=409, 
            detail="Invalid email"
        )

    result = await session.exec(
        select(DimLibrarian).where(DimLibrarian.email == email)
    )
    if result.first():
        raise HTTPException(
            status_code=409, 
            detail="Librarian already exists"
        )

    librarian = DimLibrarian(
        full_name=format_full_name(data_in.full_name),
        email=email
    )

    session.add(librarian)
    await session.commit()
    await session.refresh(librarian)

    return format_librarian(librarian)


# Update librarian
async def update_librarian(
    session: AsyncSession, 
    librarian_id: int, 
    data_in: LibrarianUpdate
):
    librarian = await session.get(DimLibrarian, librarian_id)

    if not librarian:
        raise HTTPException(
            status_code=404, 
            detail="Librarian not found"
        )

    data = data_in.model_dump(exclude_unset=True)

    # email update
    if "email" in data:
        email = data["email"].strip().lower()

        email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            raise HTTPException(
                status_code=409, 
                detail="Invalid email"
            )

        result = await session.exec(
            select(DimLibrarian).where(
                DimLibrarian.email == email,
                DimLibrarian.id != librarian_id
            )
        )
        if result.first():
            raise HTTPException(
                status_code=409, 
                detail="Email already in use"
            )

        librarian.email = email

    # name update
    if "full_name" in data:
        librarian.full_name = format_full_name(data["full_name"])

    await session.commit()
    await session.refresh(librarian)

    return format_librarian(librarian)


# Assign librarian to library
async def add_librarian_to_library(session, librarian_id: int, library_id: int):

    if not await session.get(DimLibrarian, librarian_id):
        raise HTTPException(
            status_code=404, 
            detail="Librarian not found"
        )

    if not await session.get(DimLibrary, library_id):
        raise HTTPException(
            status_code=404, 
            detail="Library not found"
        )

    result = await session.exec(
        select(LibrarianLibrary).where(
            LibrarianLibrary.librarian_id == librarian_id,
            LibrarianLibrary.library_id == library_id
        )
    )
    if result.first():
        return {"message": "already linked"}

    session.add(LibrarianLibrary(
        librarian_id=librarian_id,
        library_id=library_id
    ))

    await session.commit()
    return {"status": "linked"}


# Search librarians with libraries
async def search_librarians_with_libraries(
    session: AsyncSession, 
    query: str
):

    q = query.strip().lower()

    librarians = (await session.exec(
        select(DimLibrarian).where(
            or_(
                DimLibrarian.full_name.ilike(f"%{q}%"),
                DimLibrarian.email.ilike(f"%{q}%")
            )
        ).limit(10)
    )).all()

    results = []

    for lib in librarians:

        library_links = (await session.exec(
            select(LibrarianLibrary.library_id).where(
                LibrarianLibrary.librarian_id == lib.id
            )
        )).all()

        libraries = []
        if library_links:
            libraries = (await session.exec(
                select(DimLibrary).where(DimLibrary.id.in_(library_links))
            )).all()

        results.append({
            "id": lib.id,
            "full_name": format_full_name(lib.full_name),
            "email": lib.email,
            "libraries": [format_library(l) for l in libraries]
        })

    return results


# Remove link between librarian and library
async def remove_librarian_from_library(
    session: AsyncSession, 
    librarian_id: int, 
    library_id: int
):

    result = await session.exec(
        select(LibrarianLibrary).where(
            LibrarianLibrary.librarian_id == librarian_id,
            LibrarianLibrary.library_id == library_id
        )
    )
    link = result.first()

    if not link:
        raise HTTPException(
            status_code=404, 
            detail="Link not found"
        )

    await session.delete(link)
    await session.commit()

    return {"status": "unlinked"}


# Delete a librarian with all its links
async def delete_librarian(
    session: AsyncSession, 
    librarian_id: int
):

    librarian = await session.get(DimLibrarian, librarian_id)

    if not librarian:
        raise HTTPException(
            status_code=404, 
            detail="Librarian not found"
        )

    await session.delete(librarian)
    await session.commit()

    return {"status": "deleted"}