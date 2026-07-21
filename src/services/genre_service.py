# =====================================================
#                        Imports
# =====================================================

# Libraries:
from fastapi import HTTPException
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

# Models:
from models import (
    DimGenre, 
    BookGenre, 
    AuditAction, 
    EntityType
)

# Schemas:
from schemas import GenreCreate, GenreUpdate

# Services:
from services.audit_service import (
    write_audit_log, 
    write_failed_audit_log
)



# =====================================================
#                     Services
# =====================================================

# Create a new genre ervice
async def create_genre(
    session: AsyncSession,
    data_in: GenreCreate,
    payload: dict
):
    # Normalize the name of the GENRE to UPPERCASE and STRIP whitespace
    name = data_in.name.strip().title()

    # Try to find an existing GENTE
    existing = (
        await session.exec(
            select(DimGenre).where(DimGenre.name == name)
        )
    ).first()

    # If the genre already exists, raise an exception
    if existing:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.GENRE,
            description="Failed to create genre",
            error="Genre already exists",
            genre_name=data_in.name,
        )

        # Commit the transaction
        await session.commit()

        # Raise an exception
        raise HTTPException(
            status_code=409,
            detail="Genre already exists"
        )

    # Create a new genre
    genre = DimGenre(name=name)

    # Write the new genre to the database
    session.add(genre)

    # Flush the session to ensure that the genre is saved immediately
    await session.flush()

    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.GENRE,
        description=f"Created genre '{genre.name.title()}'",
        genre_id=genre.id
    )

    # Commit the transaction
    await session.commit()

    # Return the new genre
    await session.refresh(genre)

    # Return object
    return genre



# Search genres by name
async def search_genres(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # Create a query statement
    base_stmt = select(DimGenre)

    # Filter by name
    if query and query.strip():
        q = query.strip().lower()

        base_stmt = base_stmt.where(
            DimGenre.name.ilike(f"%{q}%")
        )

    # Total
    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.exec(total_stmt)).one()

    # Pagination
    stmt = base_stmt.offset(offset).limit(limit)
    result = await session.exec(stmt)
    genres = result.all()
    has_more = offset + len(genres) < total

    return {
        "items": [
            {"id": g.id, "name": g.name}
            for g in genres
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": has_more,
    }



# Update genres by id
async def update_genre(
    session: AsyncSession,
    genre_id: int,
    data_in: GenreUpdate,
    payload: dict
):
    # Check for existence
    genre = await session.get(DimGenre, genre_id)

    # Check for existence
    if not genre:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.GENRE,
            description="Failed to update genre",
            error="Genre not faund",
            genre_name=data_in.name,
        )

        # Commit the transaction
        await session.commit()

        # Raise error
        raise HTTPException(
            status_code=404,
            detail="Genre not found"
        )

    # Update data
    if data_in.name is not None:

        # Normalize the input
        name = data_in.name.strip().title()

        # Get existing
        existing = (
            await session.exec(
                select(DimGenre).where(
                    DimGenre.name == name,
                    DimGenre.id != genre_id
                )
            )
        ).first()

        # If the genre already exists, raise an error
        if existing:

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.GENRE,
                description="Failed to update genre",
                error="Genre already exists",
                genre_name=data_in.name,
            )

            # Commit the transaction
            await session.commit()

            # Raise an error
            raise HTTPException(
                status_code=409,
                detail="Genre already exists"
            )
        
        # Save old values for audit
        old_data = {
            "name": genre.name,
            "id": genre.id,
        }
        # Normalize new data for audit
        new_data = {
            "name": data_in.name,
            "id": genre.id,
        }

        # Update the name
        genre.name = name

    # Flush the session to ensure that the genre is saved immediately
    await session.flush()

    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.UPDATE,
        entity_type=EntityType.GENRE,
        description=f"Updated genre '{genre.name.title()}'",
        genre_id=genre.id,
        old_data=old_data,
        new_data=new_data
    )

    # Commit changes
    await session.commit()

    # Refresh the genre
    await session.refresh(genre)

    # Return the updated genre
    return genre



# Delete genres by ID
async def delete_genre(
    session: AsyncSession,
    genre_id: int,
    payload: dict,
    force: bool = False
):
    # Get genre
    genre = await session.get(DimGenre, genre_id)

    # Check for existence
    if not genre:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.GENRE,
            description=f"Failed to delete genre with id {genre_id}",
            error="Genre not found",
            genre_id=genre_id,
        )

        # Commit the transaction
        await session.commit()

        # Return error response
        raise HTTPException(
            status_code=404,
            detail="Genre not found"
        )

    # Check for linked books
    linked = (
        await session.exec(
            select(BookGenre).where(
                BookGenre.genre_id == genre_id
            )
        )
    ).first()

    # Check for linked books
    if linked and not force:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.GENRE,
            description=f"Failed to delete genre '{genre.name.title()}'",
            error="Genre is linked to books",
            genre_id=genre_id,
            force=force,
        )

        # Commit the transaction
        await session.commit()

        raise HTTPException(
            status_code=409,
            detail=(
                "Genre is assigned to one or more books. "
                "Use force=true to delete it together with all associations."
            )
        )

    # Save data before deletion
    genre_name = genre.name.title()
    genre_id = genre.id

    # Delete genre
    await session.delete(genre)

    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.GENRE,
        description=f"Deleted genre '{genre_name}'",
        genre_id=genre_id,
        genre_name=genre_name,
        force=force,
    )

    await session.commit()

    return {
        "status": "deleted"
    }