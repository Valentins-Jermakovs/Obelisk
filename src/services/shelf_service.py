# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException, Depends
from sqlmodel import select, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import (
    DimShelf,
    LibrarianLibrary, 
    DimLibrarian, 
    BookPosition,
    AuditAction, 
    EntityType
)
# Utils:
from utils.token_utils import validate_token
# Services:
from services.audit_service import (
    write_audit_log, 
    write_failed_audit_log
)


# ===================================================
#      Service code - create, update, get, delete
# ===================================================


# Helper function: Get current librarian
async def get_current_librarian(
    session: AsyncSession,
    payload: dict
) -> DimLibrarian:
    # Get the email from the token payload
    email = payload.get("email")

    if not email:
        raise HTTPException(401, "Invalid token payload")

    # Get the current librarian from the database
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
    # Get the librarian's library access link
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
    

# Search shelf by code, section
async def search_shelves(
    session: AsyncSession,
    library_id: int,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0,
):
    # Base query
    base_stmt = select(DimShelf).where(
        DimShelf.library_id == library_id
    )

    # Filtered query
    stmt = base_stmt

    if query:
        # Search by code or section
        q = query.strip().lower()
        stmt = stmt.where(
            or_(
                DimShelf.code.ilike(f"%{q}%"),
                DimShelf.section.ilike(f"%{q}%")
            )
        )

    # Pagination
    paginated_stmt = stmt.offset(offset).limit(limit)
    items = (await session.exec(paginated_stmt)).all()

    # Total shelves in library (WITHOUT filter)
    total_stmt = select(func.count(DimShelf.id)).where(
        DimShelf.library_id == library_id
    )
    total = (await session.exec(total_stmt)).one()

    returned = len(items)
    has_more = offset + len(items) < total

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
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
    # Get current librarian
    librarian = await get_current_librarian(session, payload)

    # Check librarian access to library
    await check_library_access(
        session,
        librarian.id,
        library_id
    )

    # Normalize data
    code = code.strip().upper()

    section = (
        section.strip().title()
        if section
        else None
    )

    # Check duplicate shelf in this library
    existing = (
        await session.exec(
            select(DimShelf).where(
                DimShelf.library_id == library_id,
                DimShelf.code == code
            )
        )
    ).first()

    if existing:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.SHELF,
            description=f"Failed to create shelf '{code}'",
            error="Shelf already exists",
            shelf_code=code,
            library_id=library_id,
            librarian_id=librarian.id,
        )

        # Commit log
        await session.commit()

        # Raise HTTP exception
        raise HTTPException(
            status_code=409,
            detail=f"Shelf '{code}' already exists in this library"
        )

    # Create shelf
    shelf = DimShelf(
        library_id=library_id,
        code=code,
        section=section
    )

    # Save
    session.add(shelf)

    # Flush to get ID
    await session.flush()


    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.SHELF,
        description=f"Created shelf '{shelf.code}'",
        shelf_id=shelf.id,
        library_id=shelf.library_id,
        code=shelf.code,
        section=shelf.section,
        librarian_id=librarian.id,
    )

    # Commit everything
    await session.commit()
    await session.refresh(shelf)

    return shelf


# Update shelf by ID
async def update_shelf(
    session: AsyncSession,
    shelf_id: int,
    code: str | None = None,
    section: str | None = None,
    payload: dict = Depends(validate_token)
):
    # Get shelf
    shelf = await session.get(DimShelf, shelf_id)

    if not shelf:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.SHELF,
            description=f"Failed to update shelf with id {shelf_id}",
            error="Shelf not found",
            shelf_id=shelf_id,
        )

        # Commit log
        await session.commit()

        # Raise exception
        raise HTTPException(
            status_code=404,
            detail="Shelf not found"
        )

    # Check librarian access
    librarian = await get_current_librarian(session, payload)
    # Check librarian access
    await check_library_access(session, librarian.id, shelf.library_id)

    # Save old data
    old_data = {
        "id": shelf.id,
        "library_id": shelf.library_id,
        "code": shelf.code,
        "section": shelf.section,
    }

    # Update code
    if code is not None:

        code = code.strip().upper()

        existing = (
            await session.exec(
                select(DimShelf).where(
                    DimShelf.library_id == shelf.library_id,
                    DimShelf.code == code,
                    DimShelf.id != shelf_id
                )
            )
        ).first()

        if existing:

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.SHELF,
                description=f"Failed to update shelf '{shelf.code}'",
                error="Shelf already exists",
                shelf_id=shelf.id,
                new_code=code,
            )

            # Commit log
            await session.commit()

            # Return error response
            raise HTTPException(
                status_code=409,
                detail=f"Shelf '{code}' already exists in this library"
            )

        shelf.code = code

    # Update section
    if section is not None:
        shelf.section = section.strip().title()

    # Flush changes
    await session.flush()


    # Save new data
    new_data = {
        "id": shelf.id,
        "library_id": shelf.library_id,
        "code": shelf.code,
        "section": shelf.section,
    }


    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.UPDATE,
        entity_type=EntityType.SHELF,
        description=f"Updated shelf '{shelf.code}'",
        shelf_id=shelf.id,
        old_data=old_data,
        new_data=new_data,
        librarian_id=librarian.id,
    )

    await session.commit()
    await session.refresh(shelf)

    return shelf


# Delete shelf by ID
async def delete_shelf(
    session: AsyncSession,
    shelf_id: int,
    force: bool = False,
    payload: dict = Depends(validate_token)
):
    # Check if the shelf exists
    shelf = await session.get(DimShelf, shelf_id)

    if not shelf:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.SHELF,
            description=f"Failed to delete shelf with id {shelf_id}",
            error="Shelf not found",
            shelf_id=shelf_id,
        )

        # Commit log
        await session.commit()

        # Raise exception
        raise HTTPException(
            status_code=404, 
            detail="Shelf not found"
        )

    # Get current librarian and check library access
    librarian = await get_current_librarian(session, payload)
    # Check library access
    await check_library_access(session, librarian.id, shelf.library_id)

    # Check linked positions
    positions = (await session.exec(
        select(BookPosition).where(
            BookPosition.shelf_id == shelf_id
        )
    )).all()


    # Block deletion without force
    if positions and not force:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.SHELF,
            description=f"Failed to delete shelf '{shelf.code}'",
            error="Shelf has books assigned",
            shelf_id=shelf.id,
            library_id=shelf.library_id,
            code=shelf.code,
            section=shelf.section,
            linked_positions=len(positions),
            force=force,
        )

        # Commit log
        await session.commit()

        # Return failed response
        raise HTTPException(
            status_code=409,
            detail="Shelf has books assigned. Use force=true to delete."
        )

    # Save old data
    old_data = {
        "id": shelf.id,
        "library_id": shelf.library_id,
        "code": shelf.code,
        "section": shelf.section,
        "deleted_positions": len(positions),
    }

    # Delete the shelf
    await session.delete(shelf)

    # Flush changes
    await session.flush()


    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.SHELF,
        description=f"Deleted shelf '{old_data['code']}'",
        shelf_id=shelf_id,
        old_data=old_data,
        force=force,
        deleted_positions=len(positions),
        librarian_id=librarian.id,
    )

    await session.commit()

    return {
        "status": "deleted"
    }