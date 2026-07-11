# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
import re
# Models:
from models import (
    DimLibrarian, 
    DimLibrary, 
    LibrarianLibrary,
    AuditAction, 
    EntityType
)
# Schemas:
from schemas.librarian import LibrarianCreate, LibrarianUpdate
# Utils:
from utils.formatters import (
    format_full_name, 
    format_library, 
    format_librarian
)
# Services:
from services.audit_service import (
    write_audit_log, 
    write_failed_audit_log
)


# ===================================================
#      Service code - create, update, get, delete
# ===================================================


# Create librarian
async def create_librarian(
    session: AsyncSession, 
    data_in: LibrarianCreate,
    payload: dict
):
    # Normalize the name of the LIBRARIAN to UPPERCASE and STRIP whitespace
    email = data_in.email.strip().lower()

    # Validate the email format
    email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):

        # Write audit log for failed librarian creation
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.LIBRARIAN,
            description="Failed to create librarian",
            error="Invalid email",
            full_name=format_full_name(data_in.full_name),
            email=email,
        )

        # Commit log
        await session.commit()

        # Raise an error
        raise HTTPException(
            status_code=400, 
            detail="Invalid email"
        )

    # Try to find an existing LIBRARIAN
    result = await session.exec(
        select(DimLibrarian).where(DimLibrarian.email == email)
    )
    if result.first():

        # Write audit log for failed librarian creation
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.LIBRARIAN,
            description="Failed to create librarian",
            error="Librarian already exists",
            full_name=format_full_name(data_in.full_name),
            email=email,
        )

        # Commit log
        await session.commit()

        # Raise an error
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

    # Flush to get generated ID
    await session.flush()

    # Audit success
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.LIBRARIAN,
        description=f"Created librarian '{librarian.full_name}'",
        librarian_id=librarian.id,
        full_name=librarian.full_name,
        email=librarian.email,
    )

    # Commit everything
    await session.commit()

    # Refresh object
    await session.refresh(librarian)

    # Return data
    return format_librarian(librarian)


# Update librarian by ID
async def update_librarian(
    session: AsyncSession, 
    librarian_id: int, 
    data_in: LibrarianUpdate,
    payload: dict
):
    # Get the librarian by ID
    librarian = await session.get(DimLibrarian, librarian_id)

    if not librarian:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.LIBRARIAN,
            description=f"Failed to update librarian with id {librarian_id}",
            error="Librarian not found",
            librarian_id=librarian_id,
        )

        # Commit log
        await session.commit()

        # Raise an error
        raise HTTPException(
            status_code=404, 
            detail="Librarian not found"
        )

    # Save old data
    old_data = {
        "full_name": librarian.full_name,
        "email": librarian.email,
    }

    # Request data
    data = data_in.model_dump(exclude_unset=True)

    # Email update
    if "email" in data:
        email = data["email"].strip().lower()

        # Validate the email format
        email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"

        if not re.match(email_regex, email):

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.LIBRARIAN,
                description=f"Failed to update librarian '{librarian.full_name}'",
                error="Invalid email",
                librarian_id=librarian.id,
                email=email,
            )

            # Raise an error
            await session.commit()

            # Raise an error
            raise HTTPException(
                status_code=400, 
                detail="Invalid email"
            )

        # Check for duplicate emails
        result = await session.exec(
            select(DimLibrarian).where(
                DimLibrarian.email == email,
                DimLibrarian.id != librarian_id
            )
        )

        # If there is a duplicate email, raise an error
        if result.first():

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.LIBRARIAN,
                description=f"Failed to update librarian '{librarian.full_name}'",
                error="Email already in use",
                librarian_id=librarian.id,
                email=email,
            )

            # Commit log
            await session.commit()

            # Raise an error
            raise HTTPException(
                status_code=409, 
                detail="Email already in use"
            )

        librarian.email = email

    # Update name
    if "full_name" in data:
        librarian.full_name = format_full_name(data["full_name"])

    # Flush changes
    await session.flush()

    # Save new data
    new_data = {
        "full_name": librarian.full_name,
        "email": librarian.email,
    }

    # Audit success
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.UPDATE,
        entity_type=EntityType.LIBRARIAN,
        description=f"Updated librarian '{librarian.full_name}'",
        librarian_id=librarian.id,
        old_data=old_data,
        new_data=new_data,
    )

    # Commit everything    
    await session.commit()

    # Refresh object
    await session.refresh(librarian)

    # Return data
    return format_librarian(librarian)


# Assign librarian to library
async def add_librarian_to_library(
    session: AsyncSession, 
    librarian_id: int, 
    library_id: int,
    payload: dict
):

    # Check librarian
    librarian = await session.get(DimLibrarian, librarian_id)

    if not librarian:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.LIBRARIAN,
            description=f"Failed to assign librarian {librarian_id} to library {library_id}",
            error="Librarian not found",
            librarian_id=librarian_id,
            library_id=library_id,
        )

        # Commit log
        await session.commit()

        # Return error response
        raise HTTPException(
            status_code=404,
            detail="Librarian not found"
        )

    # Check library
    library = await session.get(DimLibrary, library_id)

    if not library:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.LIBRARIAN,
            description=f"Failed to assign librarian '{librarian.full_name}' to library {library_id}",
            error="Library not found",
            librarian_id=librarian.id,
            library_id=library_id,
        )

        # Commit log
        await session.commit()

        # Return error response
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

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.LIBRARIAN,
            description=(
                f"Failed to assign librarian '{librarian.full_name}' "
                f"to library '{library.name.title()}'"
            ),
            error="Relationship already exists",
            librarian_id=librarian.id,
            library_id=library.id,
        )

        # Commit log
        await session.commit()

        # Return error response
        raise HTTPException(
            status_code=409,
            detail="Librarian is already assigned to this library"
        )

    # Create a new librarian library relationship
    session.add(LibrarianLibrary(
        librarian_id=librarian_id,
        library_id=library_id
    ))

    # Flush the session to ensure that the relationship is saved
    await session.flush()

    # Audit success
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.LIBRARIAN,
        description=(
            f"Assigned librarian '{librarian.full_name}' "
            f"to library '{library.name.title()}'"
        ),
        librarian_id=librarian.id,
        library_id=library.id,
        librarian_name=librarian.full_name,
        library_name=library.name.title(),
    )

    # Commit the changes to the database
    await session.commit()

    return {
        "status": "linked"
    }


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
    library_id: int,
    payload: dict
):
    
    # Get librarian and library (for audit)
    librarian = await session.get(DimLibrarian, librarian_id)
    library = await session.get(DimLibrary, library_id)

    # Get the link between librarian and library
    result = await session.exec(
        select(LibrarianLibrary).where(
            LibrarianLibrary.librarian_id == librarian_id,
            LibrarianLibrary.library_id == library_id
        )
    )
    link = result.first()

    # Check existence
    if not link:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.LIBRARIAN,
            description=f"Failed to remove librarian {librarian_id} from library {library_id}",
            error="Relationship not found",
            librarian_id=librarian_id,
            library_id=library_id,
        )

        # Commit log
        await session.commit()

        # Raise exception
        raise HTTPException(
            status_code=404,
            detail="Link not found"
        )

    # Save data for audit
    librarian_name = librarian.full_name if librarian else None
    library_name = library.name.title() if library else None

    # Remove the link
    await session.delete(link)

    await session.flush()

    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.LIBRARIAN,
        description=(
            f"Removed librarian '{librarian_name}' "
            f"from library '{library_name}'"
        ),
        librarian_id=librarian_id,
        library_id=library_id,
        librarian_name=librarian_name,
        library_name=library_name,
    )


    await session.commit()

    return {
        "status": "unlinked"
    }


# Delete librarian with all links
async def delete_librarian(
    session: AsyncSession,
    librarian_id: int,
    payload: dict,
    force: bool = False
):
    # Check if librarian exists
    librarian = await session.get(
        DimLibrarian,
        librarian_id
    )

    if not librarian:

        # Write error audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.LIBRARIAN,
            description=f"Failed to delete librarian with id {librarian_id}",
            error="Librarian not found",
            librarian_id=librarian_id,
        )

        # Commit log
        await session.commit()

        # Raise exception
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


    # Block deletion if linked libraries exist
    if libraries_count > 0 and not force:

        # Write error audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.LIBRARIAN,
            description=f"Failed to delete librarian '{librarian.full_name}'",
            error="Librarian has linked libraries",
            librarian_id=librarian.id,
            librarian_name=librarian.full_name,
            linked_libraries=libraries_count,
            force=force,
        )

        # Commit log
        await session.commit()

        # Return error response
        raise HTTPException(
            status_code=409,
            detail=(
                f"Librarian is assigned to "
                f"{libraries_count} libraries. "
                "Use force=true to delete."
            )
        )


    # Save old data
    old_data = {
        "id": librarian.id,
        "full_name": librarian.full_name,
        "email": librarian.email,
    }

    # Delete librarian
    await session.delete(librarian)

    await session.flush()

    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.LIBRARIAN,
        description=f"Deleted librarian '{librarian.full_name}'",
        librarian_id=librarian.id,
        librarian_name=librarian.full_name,
        old_data=old_data,
        force=force,
        removed_libraries_links=libraries_count,
    )
    
    # Commit changes
    await session.commit()

    return {
        "status": "deleted",
        "removed_libraries_links": libraries_count
    }