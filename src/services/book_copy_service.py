# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
# Helpers:
from utils.service_utils import (
    _validate_librarian_access_to_library,
    _get_copy_library_id,
    _get_last_loan,
    _get_accessible_library_ids,
    _check_position_is_available
)
# Schemas:
from schemas.book_copy import BookCopyCreate, BookCopyUpdate
# Models:
from models import (
    DimBook,
    DimBookCopy,
    DimShelf,
    BookPosition,
    LoanStatus,
    FactLoan,
    AuditAction, 
    EntityType
)
# Services:
from services.audit_service import (
    write_audit_log, 
    write_failed_audit_log
)


# ===================================================
#      Service code - create, update, get, delete
# ===================================================

# Create physical book copy
async def create_book_copy(
    session: AsyncSession,
    data: BookCopyCreate,
    payload: dict
):

    # Check librarian access
    await _validate_librarian_access_to_library(
        session,
        payload,
        data.library_id
    )

    # Check book exists
    book = await session.get(
        DimBook,
        data.book_id
    )

    if not book:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.BOOK_COPY,
            description="Failed to create book copy",
            error="Book not found",
            book_id=data.book_id,
        )

        # Commit audit log
        await session.commit()

        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )

    # Check shelf exists
    shelf = await session.get(
        DimShelf,
        data.shelf_id
    )

    if not shelf:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.BOOK_COPY,
            description="Failed to create book copy",
            error="Shelf not found",
            shelf_id=data.shelf_id,
        )

        # Commit audit log
        await session.commit()

        raise HTTPException(
            status_code=404,
            detail="Shelf not found"
        )

    # Shelf must belong to selected library
    if shelf.library_id != data.library_id:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.BOOK_COPY,
            description="Failed to create book copy",
            error="Shelf belongs to another library",
            shelf_id=shelf.id,
            shelf_library_id=shelf.library_id,
            requested_library_id=data.library_id,
        )

        # Commit audit log
        await session.commit()

        raise HTTPException(
            status_code=409,
            detail="Shelf belongs to another library"
        )

    # Normalize inventory code
    inventory_code = data.inventory_code.strip().upper()

    # Inventory code must be unique
    existing = (
        await session.exec(
            select(DimBookCopy).where(
                DimBookCopy.inventory_code == inventory_code
            )
        )
    ).first()

    if existing:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.BOOK_COPY,
            description="Failed to create book copy",
            error="Inventory code already exists",
            inventory_code=inventory_code,
        )

        # Commit audit log
        await session.commit()

        raise HTTPException(
            status_code=409,
            detail="Inventory code already exists"
        )

    # Check that shelf position is free
    await _check_position_is_available(
        session,
        data.shelf_id,
        data.row,
        data.column,
        data.depth
    )

    # Create book copy
    copy = DimBookCopy(
        book_id=data.book_id,
        inventory_code=inventory_code,
        condition=data.condition
    )

    session.add(copy)

    # Flush to get generated ID
    await session.flush()

    # Create physical position
    position = BookPosition(
        book_copy_id=copy.id,
        shelf_id=data.shelf_id,
        row=data.row,
        column=data.column,
        depth=data.depth
    )

    session.add(position)

    # Write success audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.BOOK_COPY,
        description=f"Created book copy '{copy.inventory_code}'",
        copy_id=copy.id,
        book_id=book.id,
        book_title=book.title,
        library_id=data.library_id,
        shelf_id=data.shelf_id,
        inventory_code=copy.inventory_code,
        condition=copy.condition,
        position={
            "row": position.row,
            "column": position.column,
            "depth": position.depth,
        },
    )

    # Commit changes
    await session.commit()

    # Refresh object
    await session.refresh(copy)

    return copy


# Update physical book copy
async def update_book_copy(
    session: AsyncSession,
    copy_id: int,
    data: BookCopyUpdate,
    payload: dict
):

    # Get copy
    copy = await session.get(
        DimBookCopy,
        copy_id
    )

    if not copy:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.BOOK_COPY,
            description=f"Failed to update book copy with id {copy_id}",
            error="Book copy not found",
            copy_id=copy_id,
        )

        await session.commit()

        raise HTTPException(
            status_code=404,
            detail="Book copy not found"
        )


    # Save old data for audit
    old_data = {
        "id": copy.id,
        "book_id": copy.book_id,
        "inventory_code": copy.inventory_code,
        "condition": copy.condition,
    }


    # Check librarian access
    library_id = await _get_copy_library_id(
        session,
        copy_id
    )

    await _validate_librarian_access_to_library(
        session,
        payload,
        library_id
    )


    # Get position
    position = (
        await session.exec(
            select(BookPosition).where(
                BookPosition.book_copy_id == copy_id
            )
        )
    ).first()


    if not position:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.BOOK_COPY,
            description=f"Failed to update book copy '{copy.inventory_code}'",
            error="Book position not found",
            copy_id=copy.id,
        )

        await session.commit()

        raise HTTPException(
            status_code=404,
            detail="Book position not found"
        )


    # Add old position data
    old_data["position"] = {
        "shelf_id": position.shelf_id,
        "row": position.row,
        "column": position.column,
        "depth": position.depth,
    }


    # Get update fields
    update_data = data.model_dump(
        exclude_unset=True
    )


    # Target position values
    target_shelf_id = update_data.get(
        "shelf_id",
        position.shelf_id
    )

    target_row = update_data.get(
        "row",
        position.row
    )

    target_column = update_data.get(
        "column",
        position.column
    )

    target_depth = update_data.get(
        "depth",
        position.depth
    )


    # Check new position availability
    if any(
        field in update_data
        for field in (
            "shelf_id",
            "row",
            "column",
            "depth"
        )
    ):

        await _check_position_is_available(
            session,
            target_shelf_id,
            target_row,
            target_column,
            target_depth,
            exclude_copy_id=copy_id
        )


    # Update inventory code
    if "inventory_code" in update_data:

        inventory_code_value = update_data["inventory_code"]

        if inventory_code_value is not None:

            inventory_code = (
                inventory_code_value
                .strip()
                .upper()
            )


            if not inventory_code:

                await write_failed_audit_log(
                    session=session,
                    payload=payload,
                    action=AuditAction.UPDATE,
                    entity_type=EntityType.BOOK_COPY,
                    description=f"Failed to update book copy '{copy.inventory_code}'",
                    error="Inventory code cannot be empty",
                    copy_id=copy.id,
                )

                await session.commit()

                raise HTTPException(
                    status_code=422,
                    detail="Inventory code cannot be empty"
                )


            existing = (
                await session.exec(
                    select(DimBookCopy).where(
                        DimBookCopy.inventory_code == inventory_code,
                        DimBookCopy.id != copy_id
                    )
                )
            ).first()


            if existing:

                await write_failed_audit_log(
                    session=session,
                    payload=payload,
                    action=AuditAction.UPDATE,
                    entity_type=EntityType.BOOK_COPY,
                    description=f"Failed to update book copy '{copy.inventory_code}'",
                    error="Inventory code already exists",
                    copy_id=copy.id,
                    inventory_code=inventory_code,
                )

                await session.commit()

                raise HTTPException(
                    status_code=409,
                    detail="Inventory code already exists"
                )


            copy.inventory_code = inventory_code


    # Update condition
    if (
        "condition" in update_data
        and update_data["condition"] is not None
    ):
        copy.condition = update_data["condition"]



    # Update shelf
    if (
        "shelf_id" in update_data
        and update_data["shelf_id"] is not None
    ):

        shelf = await session.get(
            DimShelf,
            update_data["shelf_id"]
        )


        if not shelf:

            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.BOOK_COPY,
                description=f"Failed to update book copy '{copy.inventory_code}'",
                error="Shelf not found",
                copy_id=copy.id,
                shelf_id=update_data["shelf_id"],
            )

            await session.commit()

            raise HTTPException(
                status_code=404,
                detail="Shelf not found"
            )


        if shelf.library_id != library_id:

            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.BOOK_COPY,
                description=f"Failed to update book copy '{copy.inventory_code}'",
                error="Shelf belongs to another library",
                copy_id=copy.id,
                shelf_id=shelf.id,
            )

            await session.commit()

            raise HTTPException(
                status_code=409,
                detail="Shelf belongs to another library"
            )


        position.shelf_id = shelf.id



    # Update coordinates
    if "row" in update_data and update_data["row"] is not None:
        position.row = update_data["row"]

    if "column" in update_data and update_data["column"] is not None:
        position.column = update_data["column"]

    if "depth" in update_data and update_data["depth"] is not None:
        position.depth = update_data["depth"]



    # Save new data for audit
    new_data = {
        "id": copy.id,
        "book_id": copy.book_id,
        "inventory_code": copy.inventory_code,
        "condition": copy.condition,
        "position": {
            "shelf_id": position.shelf_id,
            "row": position.row,
            "column": position.column,
            "depth": position.depth,
        }
    }


    # Write success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.UPDATE,
        entity_type=EntityType.BOOK_COPY,
        description=f"Updated book copy '{copy.inventory_code}'",
        copy_id=copy.id,
        old_data=old_data,
        new_data=new_data,
    )


    # Commit changes
    await session.commit()

    # Refresh object
    await session.refresh(copy)


    return copy


# Delete physical book copy
async def delete_book_copy(
    session: AsyncSession,
    copy_id: int,
    payload: dict
):

    # Get copy
    copy = await session.get(
        DimBookCopy,
        copy_id
    )

    if not copy:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.BOOK_COPY,
            description=f"Failed to delete book copy with id {copy_id}",
            error="Book copy not found",
            copy_id=copy_id,
        )

        # Commit audit log
        await session.commit()

        raise HTTPException(
            status_code=404,
            detail="Book copy not found"
        )


    # Save old data for audit
    old_data = {
        "id": copy.id,
        "book_id": copy.book_id,
        "inventory_code": copy.inventory_code,
        "condition": copy.condition,
    }


    # Check librarian access
    library_id = await _get_copy_library_id(
        session,
        copy_id
    )

    await _validate_librarian_access_to_library(
        session,
        payload,
        library_id
    )


    # Get last loan
    loan = await _get_last_loan(
        session,
        copy_id
    )


    if loan:

        # Add loan information to audit data
        old_data["last_loan"] = {
            "loan_id": loan.id,
            "reader_id": loan.reader_id,
            "status": loan.status,
            "fine_amount": loan.fine_amount,
        }


        # Check fine
        if loan.fine_amount > 0:

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.DELETE,
                entity_type=EntityType.BOOK_COPY,
                description=f"Failed to delete book copy '{copy.inventory_code}'",
                error="Book copy has unpaid fine",
                copy_id=copy.id,
                fine_amount=loan.fine_amount,
            )

            await session.commit()

            raise HTTPException(
                status_code=409,
                detail="Book copy has unpaid fine"
            )


        # Check status
        if loan.status not in (
            LoanStatus.RETURNED,
            LoanStatus.LOST
        ):

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.DELETE,
                entity_type=EntityType.BOOK_COPY,
                description=f"Failed to delete book copy '{copy.inventory_code}'",
                error="Book copy is currently borrowed",
                copy_id=copy.id,
                loan_id=loan.id,
                loan_status=loan.status,
            )

            await session.commit()

            raise HTTPException(
                status_code=409,
                detail="Book copy is currently borrowed"
            )


    # Delete position
    position = (
        await session.exec(
            select(BookPosition).where(
                BookPosition.book_copy_id == copy_id
            )
        )
    ).first()


    if position:

        # Save position data before deletion
        old_data["position"] = {
            "shelf_id": position.shelf_id,
            "row": position.row,
            "column": position.column,
            "depth": position.depth,
        }

        await session.delete(position)


    # Delete copy
    await session.delete(copy)

    # Write success audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.BOOK_COPY,
        description=f"Deleted book copy '{copy.inventory_code}'",
        copy_id=copy.id,
        old_data=old_data,
    )


    # Commit changes
    await session.commit()


    return {
        "status": "deleted",
        "copy_id": copy_id
    }


# Search physical book copies
async def search_book_copies(
    session: AsyncSession,
    payload: dict,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    
    # Last loan subquery for book copies with the latest loan
    last_loan_subquery = (
        select(
            FactLoan.book_copy_id,
            func.max(FactLoan.id).label("last_loan_id")
        )
        .group_by(
            FactLoan.book_copy_id
        )
        .subquery()
    )


    # Main query - search by book title or code
    stmt = (
        select(
            DimBookCopy,
            DimBook.title,
            DimShelf.library_id,
            DimShelf.code,
            BookPosition.row,
            BookPosition.column,
            BookPosition.depth,
            FactLoan.status
        )
        .join(
            DimBook,
            DimBook.id == DimBookCopy.book_id
        )
        .join(
            BookPosition,
            BookPosition.book_copy_id == DimBookCopy.id
        )
        .join(
            DimShelf,
            DimShelf.id == BookPosition.shelf_id
        )
        .outerjoin(
            last_loan_subquery,
            last_loan_subquery.c.book_copy_id == DimBookCopy.id
        )
        .outerjoin(
            FactLoan,
            FactLoan.id == last_loan_subquery.c.last_loan_id
        )
    )

    # Library access
    library_ids = await _get_accessible_library_ids(
        session,
        payload
    )

    if library_ids is not None:
        # Filter by library
        stmt = stmt.where(
            DimShelf.library_id.in_(library_ids)
        )



    # Search
    if query:

        # Normalize query data
        q = query.strip().lower()

        # Search in title, inventory code and shelf code
        if q:
            stmt = stmt.where(
                or_(
                    DimBook.title.ilike(
                        f"%{q}%"
                    ),

                    DimBookCopy.inventory_code.ilike(
                        f"%{q}%"
                    ),

                    DimShelf.code.ilike(
                        f"%{q}%"
                    )
                )
            )


    # Count
    count_stmt = select(
        func.count()
    ).select_from(
        stmt.subquery()
    )
    # Count total
    total = (
        await session.exec(count_stmt)
    ).one()


    # Pagination
    stmt = (
        stmt
        .order_by(
            DimBook.title
        )
        .offset(offset)
        .limit(limit)
    )

    result = await session.exec(stmt)
    rows = result.all()


    # Response
    items = []

    # Loop through rows
    for (
        copy,
        title,
        library_id,
        shelf_code,
        row,
        column,
        depth,
        loan_status
    ) in rows:

        # Availability
        if loan_status is None:
            availability = "available"
        elif loan_status == LoanStatus.RETURNED:
            availability = "available"
        else:
            availability = loan_status

        # Add to list
        items.append(
            {
                "id": copy.id,
                "book_id": copy.book_id,
                "title": title,
                "inventory_code": copy.inventory_code,
                "condition": copy.condition,
                "library_id": library_id,
                "shelf": {
                    "code": shelf_code,
                    "row": row,
                    "column": column,
                    "depth": depth
                },
                "loan_status": availability
            }
        )


    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(items)
    }