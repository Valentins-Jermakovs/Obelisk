# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
import re
# Models:
from models import DimReader, FactLoan, LoanStatus
# Schemas:
from schemas.reader import ReaderCreate, ReaderUpdate
# Utils:
from utils.formatters import format_full_name



# ===================================================
#      Service code - create, update, get, delete
# ===================================================

# Create reader
async def create_reader(
    session: AsyncSession,
    data_in: ReaderCreate
):
    # Normalize the name of the READER to UPP
    email = data_in.email.strip().lower()

    # Check the format of the EMAIL
    email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        raise HTTPException(
            status_code=409,
            detail="Invalid email"
        )

    # Check if the EMAIL already exists
    existing = (
        await session.exec(
            select(DimReader).where(
                DimReader.email == email
            )
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Reader already exists"
        )

    # Create the new READER
    reader = DimReader(
        full_name=format_full_name(data_in.full_name),
        email=email
    )

    # Add the new READER to the database
    session.add(reader)
    await session.commit()
    await session.refresh(reader)

    return {
        "id": reader.id,
        "full_name": reader.full_name,
        "email": reader.email
    }


# Update reader by ID
async def update_reader(
    session: AsyncSession,
    reader_id: int,
    data_in: ReaderUpdate
):
    # Get the reader by ID
    reader = await session.get(DimReader, reader_id)

    if not reader:
        raise HTTPException(
            status_code=404,
            detail="Reader not found"
        )

    # Translate data to model fields
    data = data_in.model_dump(exclude_unset=True)

    # Update email
    if "email" in data:
        # Remove leading and trailing spaces from the email
        email = data["email"].strip().lower()

        # Check the format of the email
        email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            raise HTTPException(
                status_code=409,
                detail="Invalid email"
            )

        # Check for uniqueness of the email
        existing = (
            await session.exec(
                select(DimReader).where(
                    DimReader.email == email,
                    DimReader.id != reader_id
                )
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already in use"
            )

        reader.email = email

    # Update full name
    if "full_name" in data:
        reader.full_name = format_full_name(data["full_name"])


    # Update READER
    await session.commit()
    await session.refresh(reader)

    return {
        "id": reader.id,
        "full_name": reader.full_name,
        "email": reader.email
    }

# Search reader by email, full_name
async def search_readers(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # Create a query
    base_stmt = select(DimReader)

    # Query by email or full_name
    if query and query.strip():
        q = query.strip().lower()

        base_stmt = base_stmt.where(
            or_(
                DimReader.full_name.ilike(f"%{q}%"),
                DimReader.email.ilike(f"%{q}%")
            )
        )

    # Total count
    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.exec(total_stmt)).one()

    # Pagination
    stmt = base_stmt.offset(offset).limit(limit)
    result = await session.exec(stmt)
    readers = result.all()

    return {
        "items": [
            {
                "id": r.id,
                "full_name": format_full_name(r.full_name),
                "email": r.email
            }
            for r in readers
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(readers)
    }


# Delete reader by ID
async def delete_reader(
    session: AsyncSession,
    reader_id: int
):
    # Get reader by ID
    reader = await session.get(DimReader, reader_id)

    if not reader:
        raise HTTPException(
            status_code=404,
            detail="Reader not found"
        )

    # Get reader linked Loans
    loans = (
        await session.exec(
            select(FactLoan).where(
                FactLoan.reader_id == reader_id
            )
        )
    ).all()

    # Check if reader has active, overdue or lost loans
    if any(
        loan.status in (
            LoanStatus.ACTIVE,
            LoanStatus.OVERDUE,
            LoanStatus.LOST
        )
        for loan in loans
    ):
        raise HTTPException(
            status_code=409,
            detail="Reader has active loans"
        )

    # Check if reader has unpaid fines
    if any(loan.fine_amount > 0 for loan in loans):
        raise HTTPException(
            status_code=409,
            detail="Reader has unpaid fines"
        )

    # Delete reader from the database
    await session.delete(reader)
    await session.commit()

    return {
        "status": "deleted"
    }