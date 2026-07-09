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
    FactLoan
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
        raise HTTPException(
            status_code=404,
            detail="Shelf not found"
        )


    # Shelf must belong to selected library
    if shelf.library_id != data.library_id:
        raise HTTPException(
            status_code=409,
            detail="Shelf belongs to another library"
        )


    # Inventory code must be unique
    existing = (
        await session.exec(
            select(DimBookCopy).where(
                DimBookCopy.inventory_code == data.inventory_code.strip()
            )
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Inventory code already exists"
        )


    await _check_position_is_available(
        session,
        data.shelf_id,
        data.row,
        data.column,
        data.depth
    )

    # Create copy
    copy = DimBookCopy(
        book_id=data.book_id,
        inventory_code=data.inventory_code.strip().upper(),
        condition=data.condition
    )

    session.add(copy)
    await session.flush()


    # Create position
    position = BookPosition(
        book_copy_id=copy.id,
        shelf_id=data.shelf_id,
        row=data.row,
        column=data.column,
        depth=data.depth
    )

    session.add(position)
    await session.commit()
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
        raise HTTPException(
            status_code=404,
            detail="Book copy not found"
        )


    # Check librarian access
    # Get library id of book copy
    library_id = await _get_copy_library_id(
        session,
        copy_id
    )

    # Validate librarian access to library
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
        raise HTTPException(
            status_code=404,
            detail="Book position not found"
        )

    # Set attributes of copy update data
    update_data = data.model_dump(
        exclude_unset=True
    )

    target_shelf_id = update_data.get("shelf_id", position.shelf_id)
    target_row = update_data.get("row", position.row)
    target_column = update_data.get("column", position.column)
    target_depth = update_data.get("depth", position.depth)

    if any(field in update_data for field in ("shelf_id", "row", "column", "depth")):
        await _check_position_is_available(
            session,
            target_shelf_id,
            target_row,
            target_column,
            target_depth,
            exclude_copy_id=copy_id
        )

    # Check for new inventory code
    if "inventory_code" in update_data:

        # Check for duplicate code
        inventory_code_value = update_data["inventory_code"]

        if inventory_code_value is not None:

            # Normalize the inventory code
            inventory_code = inventory_code_value.strip().upper()

            # If the code is empty, it's not a duplicate
            if not inventory_code:
                raise HTTPException(
                    status_code=422,
                    detail="Inventory code cannot be empty"
                )

            # Check for duplicate code
            existing = (
                await session.exec(
                    select(DimBookCopy).where(
                        DimBookCopy.inventory_code == inventory_code,
                        DimBookCopy.id != copy_id
                    )
                )
            ).first()

            # If a duplicate code exists, raise an error
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail="Inventory code already exists"
                )

            # Update inventory code in the session
            copy.inventory_code = inventory_code


    # Condition
    if "condition" in update_data and update_data["condition"] is not None:
        copy.condition = update_data["condition"]


    # Update shelf position if it is set
    if "shelf_id" in update_data and update_data["shelf_id"] is not None:

        # Get the shelf from the session
        shelf = await session.get(
            DimShelf,
            update_data["shelf_id"]
        )

        # If the shelf does not belong to the library, raise an error
        if not shelf:
            raise HTTPException(
                status_code=404,
                detail="Shelf not found"
            )

        # If the shelf belongs to another library, raise an error
        if shelf.library_id != library_id:
            raise HTTPException(
                status_code=409,
                detail="Shelf belongs to another library"
            )

        # Set the shelf id of the position
        position.shelf_id = shelf.id


    # Coordinates
    # Check if row are provided
    if "row" in update_data and update_data["row"] is not None:
        position.row = update_data["row"]
    # Check if column are provided
    if "column" in update_data and update_data["column"] is not None:
        position.column = update_data["column"]
    # Check if depth is provided
    if "depth" in update_data and update_data["depth"] is not None:
        position.depth = update_data["depth"]

    # Save changes to database
    await session.commit()
    await session.refresh(copy)

    # Return book copy
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
        raise HTTPException(
            status_code=404,
            detail="Book copy not found"
        )


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


    # Check last loan
    loan = await _get_last_loan(
        session,
        copy_id
    )

    if loan:
        # Check fine
        if loan.fine_amount > 0:
            raise HTTPException(
                status_code=409,
                detail="Book copy has unpaid fine"
            )
        # Check status
        if loan.status not in (
            LoanStatus.RETURNED,
            LoanStatus.LOST
        ):
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
        await session.delete(position)


    # Delete copy
    await session.delete(copy)
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