# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
import re
# Models:
from models import DimLibrarian, DimLibrary, LibrarianLibrary
# Schemas:
from schemas.librarian import LibrarianCreate, LibrarianUpdate
# Utils:
from utils.formatters import format_full_name, format_library, format_librarian



# ===================================================
#      Service code - create, update, get, delete
# ===================================================


# Create librarian
async def create_librarian(
    session: AsyncSession, 
    data_in: LibrarianCreate
):
    # Normalize the name of the LIBRARIAN to UPPERCASE and STRIP whitespace
    email = data_in.email.strip().lower()

    # Validate the email format
    email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        raise HTTPException(
            status_code=409, 
            detail="Invalid email"
        )

    # Try to find an existing LIBRARIAN
    result = await session.exec(
        select(DimLibrarian).where(DimLibrarian.email == email)
    )
    if result.first():
        raise HTTPException(
            status_code=409, 
            detail="Librarian already exists"
        )

    # Create a new LIBRARIAN
    librarian = DimLibrarian(
        full_name=format_full_name(data_in.full_name),
        email=email
    )

    # Write the new LIBRARIAN to the database
    session.add(librarian)
    await session.commit()
    await session.refresh(librarian)

    return format_librarian(librarian)


# Update librarian by ID
async def update_librarian(
    session: AsyncSession, 
    librarian_id: int, 
    data_in: LibrarianUpdate
):
    # Get the librarian by ID
    librarian = await session.get(DimLibrarian, librarian_id)

    if not librarian:
        raise HTTPException(
            status_code=404, 
            detail="Librarian not found"
        )

    # Translate the data to a dictionary
    data = data_in.model_dump(exclude_unset=True)

    # Email update
    if "email" in data:
        email = data["email"].strip().lower()

        # Validate the email format
        email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            raise HTTPException(
                status_code=409, 
                detail="Invalid email"
            )

        # Check for duplicate emails
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

    # Name update
    if "full_name" in data:
        librarian.full_name = format_full_name(data["full_name"])


    # Update the librarian in the database
    await session.commit()
    await session.refresh(librarian)

    return format_librarian(librarian)


# Assign librarian to library
async def add_librarian_to_library(
    session, 
    librarian_id: int, 
    library_id: int
):

    # Check for librarian and library existence
    if not await session.get(DimLibrarian, librarian_id):
        raise HTTPException(
            status_code=404, 
            detail="Librarian not found"
        )

    # Check for librarian and library existence
    if not await session.get(DimLibrary, library_id):
        raise HTTPException(
            status_code=404, 
            detail="Library not found"
        )

    # Check if the librarian is already assigned to the library
    result = await session.exec(
        select(LibrarianLibrary).where(
            LibrarianLibrary.librarian_id == librarian_id,
            LibrarianLibrary.library_id == library_id
        )
    )
    if result.first():
        return {"message": "already linked"}

    # Create a new librarian library relationship
    session.add(LibrarianLibrary(
        librarian_id=librarian_id,
        library_id=library_id
    ))

    # Commit the changes to the database
    await session.commit()
    return {"status": "linked"}


# Search librarians with libraries
async def search_librarians_with_libraries(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # Create a statement to retrieve all librarian libraries
    stmt = select(DimLibrarian)

    # Filtering
    if query:
        q = query.strip().lower()
        if q:
            stmt = stmt.where(
                or_(
                    DimLibrarian.full_name.ilike(f"%{q}%"),
                    DimLibrarian.email.ilike(f"%{q}%")
                )
            )

    # Total count
    total_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.exec(total_stmt)).one()

    # Pagination
    stmt = stmt.offset(offset).limit(limit)
    librarians = (await session.exec(stmt)).all()

    librarian_ids = [l.id for l in librarians]

    # Bulk fetch links
    links = (await session.exec(
        select(LibrarianLibrary).where(
            LibrarianLibrary.librarian_id.in_(librarian_ids)
        )
    )).all()

    library_ids = list(set([l.library_id for l in links]))

    # Bulk fetch libraries
    libraries = {}
    if library_ids:
        libs = (await session.exec(
            select(DimLibrary).where(DimLibrary.id.in_(library_ids))
        )).all()

        libraries = {l.id: l for l in libs}

    # Group libraries per librarian
    grouped = {lid: [] for lid in librarian_ids}

    for link in links:
        if link.library_id in libraries:
            grouped[link.librarian_id].append(
                libraries[link.library_id]
            )

    # Final result
    return {
        "items": [
            {
                "id": lib.id,
                "full_name": format_full_name(lib.full_name),
                "email": lib.email,
                "libraries": [
                    format_library(l) for l in grouped.get(lib.id, [])
                ]
            }
            for lib in librarians
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(librarians)
    }


# Remove link between librarian and library
async def remove_librarian_from_library(
    session: AsyncSession, 
    librarian_id: int, 
    library_id: int
):
    # Get the link between librarian and library
    result = await session.exec(
        select(LibrarianLibrary).where(
            LibrarianLibrary.librarian_id == librarian_id,
            LibrarianLibrary.library_id == library_id
        )
    )
    link = result.first()

    # If the link exists, remove it
    if not link:
        raise HTTPException(
            status_code=404, 
            detail="Link not found"
        )

    # Remove the link
    await session.delete(link)
    await session.commit()

    return {"status": "unlinked"}


# Delete a librarian with all its links
# Delete librarian with all links
async def delete_librarian(
    session: AsyncSession,
    librarian_id: int,
    force: bool = False,
):
    # Check if librarian exists
    librarian = await session.get(
        DimLibrarian,
        librarian_id
    )

    if not librarian:
        raise HTTPException(
            status_code=404,
            detail="Librarian not found"
        )


    # Count linked libraries
    libraries_count = await session.exec(
        select(func.count())
        .select_from(LibrarianLibrary)
        .where(
            LibrarianLibrary.librarian_id == librarian_id
        )
    )

    libraries_count = libraries_count.one()


    # If librarian has linked libraries
    if libraries_count > 0 and not force:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Librarian is assigned to "
                f"{libraries_count} libraries. "
                "Use force=true to delete."
            )
        )


    # Delete librarian
    await session.delete(librarian)

    await session.commit()


    return {
        "status": "deleted",
        "removed_libraries_links": libraries_count
    }