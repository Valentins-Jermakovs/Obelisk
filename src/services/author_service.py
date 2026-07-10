# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel import (
    select, 
    or_, 
    cast, 
    String, 
    func
)
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import (
    DimAuthor, 
    BookAuthor, 
    AuditAction, 
    EntityType
)
# Schemas:
from schemas.author import AuthorCreate, AuthorUpdate
# Services:
from services.audit_service import (
    write_audit_log, 
    write_failed_audit_log
)




# ==================================================
#      Service functions - helpers and CRUD
# ==================================================

# Normalize author's name and country
def format_author(author: DimAuthor) -> DimAuthor:
    author.name = author.name.title()

    if author.country:
        author.country = author.country.title()

    return author

# Normalize author's data
def normalize_author_data(data: dict) -> dict:
    for field in ("name", "country"):
        if data.get(field):
            data[field] = data[field].strip().lower()

    return data


# Create a new author service
async def create_author(
    session: AsyncSession,
    author_data: AuthorCreate,
    payload: dict
):
    # Convert to dict
    data = normalize_author_data(author_data.model_dump())

    # Check if the author already exists
    statement = select(DimAuthor).where(
        DimAuthor.name == data["name"]
    )

    # Execute the statement - find the author
    result = await session.exec(statement)
    existing_author = result.first()

    # If the author already exists, raise an exception
    if existing_author:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.AUTHOR,
            description="Failed to create author",
            error="Author already exists",
            name=data["name"],
        )

        # Commit the transaction
        await session.commit()

        # Raise an exception
        raise HTTPException(
            status_code=409,
            detail="Author already exists"
        )

    # Create a new author
    author = DimAuthor(**data)

    # Add author to the session
    session.add(author)

    # Flush the changes to the database
    await session.flush()

    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.AUTHOR,
        description=f"Created author '{author.name.title()}'",
        author_id=author.id,
        country=author.country,
    )

    # Commit the transaction
    await session.commit()

    # Refresh the object
    await session.refresh(author)

    # Return the author object
    return format_author(author)


# Search for authors searched by name or country, birth year
async def search_authors(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # Base query (always exists)
    stmt = select(DimAuthor)

    # Optional filtering
    if query:
        # Normalize query string
        q = query.strip().lower()

        # Ignore empty string after strip
        if q:
            # Find authors by name, country or birth year
            stmt = stmt.where(
                or_(
                    DimAuthor.name.ilike(f"%{q}%"),
                    DimAuthor.country.ilike(f"%{q}%"),
                    cast(DimAuthor.birth_year, String).ilike(f"%{q}%")
                )
            )

    # Total count (with or without filter)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.exec(count_stmt)).one()

    # Pagination
    stmt = stmt.offset(offset).limit(limit)
    result = await session.exec(stmt)
    authors = result.all()

    return {
        "items": [format_author(a) for a in authors],
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(authors)
    }


# Update an author by ID
async def update_author(
    session: AsyncSession,
    author_id: int,
    author_data: AuthorUpdate,
    payload: dict
):
    # Get the author by ID
    author = await session.get(DimAuthor, author_id)

    # If the author doesn't exist, return an error
    if not author:

        # Write an audit log for this action
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.AUTHOR,
            description=f"Failed to update author with id {author_id}",
            error="Author not found",
            author_id=author_id,
        )

        # Commit the transaction
        await session.commit()

        # Raise an error
        raise HTTPException(
            status_code=404,
            detail="Author not found"
        )

    # Normalize the data
    update_data = normalize_author_data(
        author_data.model_dump(exclude_unset=True)
    )

    # Check if the new name is unique
    if "name" in update_data:

        # Select the existing author (statement)
        statement = select(DimAuthor).where(
            DimAuthor.name == update_data["name"],
            DimAuthor.id != author_id
        )

        # Execute the statement (result)
        result = await session.exec(statement)
        existing = result.first()

        # If the author with the new name exists
        if existing:

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.AUTHOR,
                description="Failed to update author",
                error="Author with this name already exists",
                author_id=author_id,
                new_name=update_data["name"],
            )

            # Commit the transaction
            await session.commit()

            # Raise an exception
            raise HTTPException(
                status_code=409,
                detail="Author with this name already exists"
            )
        

    # Save old values for audit
    old_data = {
        key: getattr(author, key)
        for key in update_data.keys()
    }

    # Update the author's attributes
    for key, value in update_data.items():
        setattr(author, key, value)


    # Flush changes before audit
    await session.flush()


    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.UPDATE,
        entity_type=EntityType.AUTHOR,
        description=f"Updated author '{author.name.title()}'",
        author_id=author.id,
        old_data=old_data,
        new_data=update_data,
    )

    # Commit the transaction
    await session.commit()

    # Refresh the object
    await session.refresh(author)

    # Return the updated author
    return format_author(author)


# Delete an author by ID
async def delete_author(
    session: AsyncSession, 
    author_id: int,
    payload: dict,
    force: bool = False
):
    # Get the author by ID
    author = await session.get(
        DimAuthor, 
        author_id
    )

    # If the author does not exist, return an error
    if not author:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.AUTHOR,
            description=f"Failed to delete author with id {author_id}",
            error="Author not found",
            author_id=author_id,
        )

        # Commit the transaction
        await session.commit()

        # Return an error
        raise HTTPException(
            status_code=404, 
            detail="Author not found"
        )

    # Check if the user wants to force deletion
    if not force:

        links = (
            await session.exec(
                select(BookAuthor)
                .where(
                    BookAuthor.author_id == author_id
                )
            )
        ).first()

        # Check if the author has any book links
        if links:

            books_count = (
                await session.exec(
                    select(func.count())
                    .select_from(BookAuthor)
                    .where(
                        BookAuthor.author_id == author_id
                    )
                )
            ).one()

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.DELETE,
                entity_type=EntityType.AUTHOR,
                description=f"Failed to delete author '{author.name.title()}'",
                error="Author is linked to books",
                author_id=author_id,
                force=force,
            )

            # Commit the transaction
            await session.commit()

            if books_count > 0:
                # Return an output message
                return {
                    "warning": "Author is linked to books",
                    "message": "Set force=True to delete author and cascade links",
                    "books_count": books_count
                }
        
    
    # Save data before deletion
    author_name = author.name.title()
    author_country = author.country


    # Delete the author
    await session.delete(author)

    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.AUTHOR,
        description=f"Deleted author '{author_name}'",
        author_id=author_id,
        country=author_country,
        force=force,
    )


    # Commit transaction
    await session.commit()

    # Return an output message
    return {
        "status": "deleted"
    }