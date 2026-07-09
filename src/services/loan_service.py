# ===================================================
#                       imports
# ===================================================
# Libraries:
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from datetime import datetime, timezone
from sqlmodel import select, or_, func
# Helper functions
from utils.service_utils import (
    _validate_librarian_access_to_library,
    _validate_reader,
    _validate_book_copy,
    _check_copy_available,
    _validate_copy_library,
    _create_loan,
    _get_accessible_loan,
    _get_accessible_library_ids,
    _get_reader_from_payload
)
# Schemas
from schemas.loan import (
    LoanCreate,
    LoanUpdate
)
# Models:
from models import (
    LoanStatus, 
    FactLoan, 
    DimBook, 
    DimBookCopy, 
    DimReader,
    DimLibrary
)


# ===================================================
#      Service code - create, update, get, delete
# ===================================================


# Create loan service
async def create_loan(
    session: AsyncSession,
    data: LoanCreate,
    payload: dict
):
    
    # Validate access to library
    await _validate_librarian_access_to_library(
        session,
        payload,
        data.library_id
    )

    # Validate reader
    await _validate_reader(
        session,
        data.reader_id
    )

    # Validate book copy
    await _validate_book_copy(
        session,
        data.book_copy_id
    )

    # Validate library
    await _validate_copy_library(
        session,
        data.book_copy_id,
        data.library_id
    )

    # Check if copy is available
    await _check_copy_available(
        session,
        data.book_copy_id
    )

    # Create loan
    loan = await _create_loan(
        session,
        data
    )

    # Commit changes to database
    await session.commit()
    await session.refresh(loan)


    # Build response matching LoanRead schema
    # Fetch related entities
    book_copy = await session.get(DimBookCopy, loan.book_copy_id)
    book = await session.get(DimBook, book_copy.book_id)
    reader = await session.get(DimReader, loan.reader_id)
    library = await session.get(DimLibrary, loan.library_id)

    return {
        "id": loan.id,
        "status": loan.status,
        "borrowed_at": loan.borrowed_at,
        "return_date": loan.return_date,
        "fine_amount": loan.fine_amount,
        "reader": {
            "id": reader.id,
            "full_name": reader.full_name,
            "email": reader.email,
        },
        "library": {
            "id": library.id,
            "name": library.name,
            "city": library.city,
        },
        "book": {
            "id": book.id,
            "title": book.title,
            "isbn": book.isbn,
            "inventory_code": book_copy.inventory_code,
        },
    }


# Update loan
async def update_loan(
    session: AsyncSession,
    loan_id: int,
    data: LoanUpdate,
    payload: dict
) -> FactLoan:


    # 1. Get loan and check librarian access
    loan = await _get_accessible_loan(
        session,
        payload,
        loan_id
    )


    # 2. Get provided fields only
    update_data = data.model_dump(
        exclude_unset=True
    )



    # Update status
    if "status" in update_data:

        new_status = update_data["status"]

        # Returned loan is final
        if (
            loan.status == LoanStatus.RETURNED
            and new_status != LoanStatus.RETURNED
        ):
            raise HTTPException(
                status_code=409,
                detail="Returned loan cannot be reopened"
            )


        # LOST -> cannot return normally
        if (
            loan.status == LoanStatus.LOST
            and new_status == LoanStatus.ACTIVE
        ):
            raise HTTPException(
                status_code=409,
                detail="Lost loan cannot become active"
            )

        # Update fields
        loan.status = new_status


        # Auto dates
        # Set to return date for returned loans
        if new_status == LoanStatus.RETURNED:

            if loan.return_date is None:
                loan.return_date = datetime.now()

        # Lost loan should have return date
        elif new_status == LoanStatus.LOST:

            if loan.return_date is None:
                loan.return_date = datetime.now()

        # Active loan should not have return date
        elif new_status == LoanStatus.ACTIVE:

            # Active loan should not have return date
            loan.return_date = None


    # Update return date
    if "return_date" in update_data:

        new_date = update_data["return_date"]

        if new_date:

            # Normalize timezone-aware incoming date to naive UTC for comparison
            if new_date.tzinfo is not None:
                new_date = new_date.astimezone(timezone.utc).replace(tzinfo=None)

            if new_date < loan.borrowed_at:
                raise HTTPException(
                    status_code=400,
                    detail="Return date cannot be before borrowed date"
                )

        # Store naive datetime (DB uses naive datetimes)
        loan.return_date = new_date


    # Update fine
    if "fine_amount" in update_data:

        fine = update_data["fine_amount"]

        if fine < 0:
            raise HTTPException(
                status_code=400,
                detail="Fine amount cannot be negative"
            )

        loan.fine_amount = fine


    # Additional validation
    # Returned loan must have return date
    if (
        loan.status == LoanStatus.RETURNED
        and loan.return_date is None
    ):
        loan.return_date = datetime.now()


    # Active loan should not have fine
    if (
        loan.status == LoanStatus.ACTIVE
        and loan.fine_amount > 0
    ):
        raise HTTPException(
            status_code=409,
            detail="Active loan cannot have fine"
        )


    # Update loan in DB
    await session.commit()
    await session.refresh(loan)

    # Build response matching LoanRead schema
    book_copy = await session.get(DimBookCopy, loan.book_copy_id)
    book = await session.get(DimBook, book_copy.book_id)
    reader = await session.get(DimReader, loan.reader_id)
    library = await session.get(DimLibrary, loan.library_id)

    return {
        "id": loan.id,
        "status": loan.status,
        "borrowed_at": loan.borrowed_at,
        "return_date": loan.return_date,
        "fine_amount": loan.fine_amount,
        "reader": {
            "id": reader.id,
            "full_name": reader.full_name,
            "email": reader.email,
        },
        "library": {
            "id": library.id,
            "name": library.name,
            "city": library.city,
        },
        "book": {
            "id": book.id,
            "title": book.title,
            "isbn": book.isbn,
            "inventory_code": book_copy.inventory_code,
        },
    }


# Delete loan
async def delete_loan(
    session: AsyncSession,
    loan_id: int,
    payload: dict
):

    # 1. Get loan and check librarian access
    loan = await _get_accessible_loan(
        session,
        payload,
        loan_id
    )

    # 2. Check status
    if loan.status != LoanStatus.RETURNED:

        raise HTTPException(
            status_code=409,
            detail="Only returned loans can be deleted"
        )

    # 3. Check fine
    if loan.fine_amount > 0:

        raise HTTPException(
            status_code=409,
            detail="Loan with fine cannot be deleted"
        )

    # 4. Delete
    await session.delete(loan)
    await session.commit()

    return {
        "status": "deleted",
        "loan_id": loan_id
    }


# Search loan for librarian by reader, book, library
async def search_loans(
    session: AsyncSession,
    query: str | None,
    payload: dict,
    limit: int = 10,
    offset: int = 0
):

    # Base query
    stmt = (
        select(
            FactLoan,
            DimBook.title,
            DimReader.full_name,
            DimLibrary.name
        )
        .join(
            DimBookCopy,
            DimBookCopy.id == FactLoan.book_copy_id
        )
        .join(
            DimBook,
            DimBook.id == DimBookCopy.book_id
        )
        .join(
            DimReader,
            DimReader.id == FactLoan.reader_id
        )
        .join(
            DimLibrary,
            DimLibrary.id == FactLoan.library_id
        )
    )


    # Library access
    library_ids = await _get_accessible_library_ids(
        session,
        payload
    )


    # If librarian - filter only his libraries
    # If admin - library_ids will be None
    if library_ids is not None:

        stmt = stmt.where(
            FactLoan.library_id.in_(library_ids)
        )


    # Search
    if query:

        # Normalize query
        q = query.strip().lower()

        if q:
            # Search in title, full name and library names
            stmt = stmt.where(
                or_(
                    DimBook.title.ilike(
                        f"%{q}%"
                    ),

                    DimReader.full_name.ilike(
                        f"%{q}%"
                    ),

                    DimLibrary.name.ilike(
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

    # Count all records
    total = (
        await session.exec(count_stmt)
    ).one()


    # Pagination
    stmt = (
        stmt
        .order_by(
            FactLoan.borrowed_at.desc()
        )
        .offset(offset)
        .limit(limit)
    )

    # Get records
    result = await session.exec(stmt)
    loans = result.all()

    # Response
    items = []

    # Loop through records
    for loan, title, reader_name, library_name in loans:
        # Append record to list
        items.append(
            {
                "id": loan.id,
                "book_copy_id": loan.book_copy_id,
                "book_title": title,
                "reader_id": loan.reader_id,
                "reader_name": reader_name.title(),
                "library_id": loan.library_id,
                "library_name": library_name,
                "status": loan.status,
                "borrowed_at": loan.borrowed_at,
                "return_date": loan.return_date,
                "fine_amount": loan.fine_amount
            }
        )


    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(items)
    }


# Search loans for reader
async def get_reader_loans(
    session: AsyncSession,
    payload: dict,
    limit: int = 10,
    offset: int = 0
):

    # Get reader
    reader = await _get_reader_from_payload(
        session,
        payload
    )


    # Base query
    stmt = (
        select(
            FactLoan,
            DimBook.title,
            DimLibrary.name
        )
        .join(
            DimBookCopy,
            DimBookCopy.id == FactLoan.book_copy_id
        )
        .join(
            DimBook,
            DimBook.id == DimBookCopy.book_id
        )
        .join(
            DimLibrary,
            DimLibrary.id == FactLoan.library_id
        )
        .where(
            FactLoan.reader_id == reader.id
        )
    )


    # Count
    count_stmt = select(
        func.count()
    ).select_from(
        stmt.subquery()
    )

    # Total
    total = (
        await session.exec(count_stmt)
    ).one()


    # Pagination
    stmt = (
        stmt
        .offset(offset)
        .limit(limit)
        .order_by(
            FactLoan.borrowed_at.desc()
        )
    )

    # Get data from database
    result = await session.exec(stmt)
    loans = result.all()

    # Store data in list
    items = []

    # Get data from database and format it for display in UI
    for loan, book_title, library_name in loans:

        items.append(
            {
                "id": loan.id,
                "book_title": book_title,
                "book_copy_id": loan.book_copy_id,
                "library_id": loan.library_id,
                "library_name": library_name,
                "status": loan.status,
                "borrowed_at": loan.borrowed_at,
                "return_date": loan.return_date,
                "fine_amount": loan.fine_amount
            }
        )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(items)
    }