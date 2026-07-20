# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, func, or_
from fastapi import HTTPException
# Models:
from models import (
    DimPublisher,
    EntityType,
    AuditAction,
    DimBook
)
# Audit:
from services.audit_service import (
    write_audit_log,
    write_failed_audit_log,
)
# Schemas:
from schemas.publisher import PublisherUpdate



# ==================================================
#                  Publisher services
# ==================================================


# Create publisher
async def create_publisher(
    session: AsyncSession,
    name: str,
    country: str | None,
    payload: dict
):

    # Normalize publisher name
    publisher_name = name.strip().title()


    # Normalize country
    publisher_country = (
        country.strip().title()
        if country
        else None
    )


    # Check empty name
    if not publisher_name:

        # Failed audit
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.PUBLISHER,
            description="Failed to create publisher",
            error="Publisher name cannot be empty",
            name=name,
        )

        await session.commit()

        raise HTTPException(
            status_code=400,
            detail="Publisher name cannot be empty"
        )


    # Check duplicate publisher
    existing = (
        await session.exec(
            select(DimPublisher).where(
                DimPublisher.name == publisher_name
            )
        )
    ).first()


    if existing:

        # Failed audit
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.PUBLISHER,
            description="Failed to create publisher",
            error="Publisher already exists",
            name=publisher_name,
            country=publisher_country,
        )

        await session.commit()

        raise HTTPException(
            status_code=409,
            detail="Publisher already exists"
        )


    # Create publisher
    publisher = DimPublisher(
        name=publisher_name,
        country=publisher_country,
    )


    # Add to session
    session.add(publisher)


    # Flush to get generated ID
    await session.flush()


    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.PUBLISHER,
        description=f"Created publisher '{publisher.name}'",
        publisher_id=publisher.id,
        name=publisher.name,
        country=publisher.country,
    )


    # Commit transaction
    await session.commit()


    # Refresh object
    await session.refresh(publisher)


    return publisher


async def update_publisher(
    session: AsyncSession,
    publisher_id: int,
    data_in: PublisherUpdate,
    payload: dict
):

    # Get publisher
    publisher = await session.get(
        DimPublisher,
        publisher_id
    )


    if not publisher:

        # Failed audit
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.PUBLISHER,
            description=f"Failed to update publisher with id {publisher_id}",
            error="Publisher not found",
            publisher_id=publisher_id,
        )

        await session.commit()

        raise HTTPException(
            status_code=404,
            detail="Publisher not found"
        )


    # Save old data
    old_data = {
        "id": publisher.id,
        "name": publisher.name,
        "country": publisher.country,
    }


    # Get provided fields only
    data = data_in.model_dump(
        exclude_unset=True
    )


    # Update name
    if "name" in data:

        new_name = data["name"].strip().title()


        if not new_name:

            # Failed audit
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.PUBLISHER,
                description=f"Failed to update publisher '{publisher.name}'",
                error="Publisher name cannot be empty",
                publisher_id=publisher.id,
            )

            await session.commit()

            raise HTTPException(
                status_code=400,
                detail="Publisher name cannot be empty"
            )


        # Check duplicate name
        existing = (
            await session.exec(
                select(DimPublisher).where(
                    DimPublisher.name == new_name,
                    DimPublisher.id != publisher_id
                )
            )
        ).first()


        if existing:

            # Failed audit
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.PUBLISHER,
                description=f"Failed to update publisher '{publisher.name}'",
                error="Publisher already exists",
                publisher_id=publisher.id,
                name=new_name,
            )

            await session.commit()

            raise HTTPException(
                status_code=409,
                detail="Publisher already exists"
            )


        publisher.name = new_name



    # Update country
    if "country" in data:

        publisher.country = (
            data["country"].strip().title()
            if data["country"]
            else None
        )


    # Flush changes
    await session.flush()


    # Save new data
    new_data = {
        "id": publisher.id,
        "name": publisher.name,
        "country": publisher.country,
    }


    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.UPDATE,
        entity_type=EntityType.PUBLISHER,
        description=f"Updated publisher '{publisher.name}'",
        publisher_id=publisher.id,
        old_data=old_data,
        new_data=new_data,
    )


    # Commit
    await session.commit()


    # Refresh
    await session.refresh(
        publisher
    )


    return publisher


async def delete_publisher(
    session: AsyncSession,
    publisher_id: int,
    force: bool = False,
    payload: dict | None = None
):

    # Get publisher
    publisher = await session.get(
        DimPublisher,
        publisher_id
    )


    if not publisher:

        # Failed audit
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.PUBLISHER,
            description=f"Failed to delete publisher with id {publisher_id}",
            error="Publisher not found",
            publisher_id=publisher_id,
        )

        await session.commit()

        raise HTTPException(
            status_code=404,
            detail="Publisher not found"
        )


    # Check linked books
    books = (
        await session.exec(
            select(DimBook).where(
                DimBook.publisher_id == publisher_id
            )
        )
    ).all()


    # Block delete without force
    if books and not force:

        # Failed audit
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.PUBLISHER,
            description=f"Failed to delete publisher '{publisher.name}'",
            error="Publisher has linked books",
            publisher_id=publisher.id,
            books_count=len(books),
        )


        await session.commit()


        raise HTTPException(
            status_code=409,
            detail=(
                "Publisher has linked books. "
                "Use force=true to delete."
            )
        )


    # Save old data for audit
    old_data = {
        "id": publisher.id,
        "name": publisher.name,
        "country": publisher.country,
        "linked_books": len(books),
    }


    # If force delete:
    # remove publisher reference from books
    if books:

        for book in books:
            book.publisher_id = None


    # Delete publisher
    await session.delete(
        publisher
    )


    # Flush
    await session.flush()


    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.PUBLISHER,
        description=f"Deleted publisher '{old_data['name']}'",
        publisher_id=publisher_id,
        old_data=old_data,
    )


    # Commit
    await session.commit()


    return {
        "status": "deleted",
        "publisher_id": publisher_id
    }


# Get publisher by ID
async def get_publisher(
    session: AsyncSession,
    publisher_id: int
):

    # Get publisher
    publisher = await session.get(
        DimPublisher,
        publisher_id
    )


    if not publisher:

        raise HTTPException(
            status_code=404,
            detail="Publisher not found"
        )


    return publisher




# Search publishers with pagination
async def search_publishers(
    session: AsyncSession,
    query: str | None = None,
    country: str | None = None,
    limit: int = 10,
    offset: int = 0,
):

    # Base query
    statement = select(
        DimPublisher
    )


    # Search
    if query:

        q = query.strip().lower()


        if q:

            statement = statement.where(
                or_(
                    DimPublisher.name.ilike(
                        f"%{q}%"
                    ),

                    DimPublisher.country.ilike(
                        f"%{q}%"
                    )
                )
            )


    # Filter by country
    if country:

        statement = statement.where(
            DimPublisher.country.ilike(
                f"%{country.strip().lower()}%"
            )
        )


    # Count total records
    count_statement = (
        select(func.count())
        .select_from(
            statement.subquery()
        )
    )


    total = (
        await session.exec(
            count_statement
        )
    ).one()



    # Newest first
    statement = (
        statement
        .order_by(
            DimPublisher.id.desc()
        )
        .offset(offset)
        .limit(limit)
    )


    # Execute
    result = await session.exec(
        statement
    )


    publishers = result.all()



    # Format response
    items = []

    for publisher in publishers:

        items.append(
            {
                "id": publisher.id,
                "name": publisher.name,
                "country": publisher.country,
            }
        )

    has_more = offset + len(items) < total

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": has_more
    }