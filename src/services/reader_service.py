# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select, or_
from sqlalchemy import func
from sqlmodel.ext.asyncio.session import AsyncSession
import re
# Models:
from models import DimReader, FactLoan, LoanStatus
# Schemas:
from schemas.reader import ReaderCreate, ReaderUpdate
# Utils:
from utils.formatters import format_full_name
# =====================================================


# ===================================================
#                       functions
# ===================================================

# Create reader
async def create_reader(
    session: AsyncSession,
    data_in: ReaderCreate
):
    email = data_in.email.strip().lower()

    email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
    if not re.match(email_regex, email):
        raise HTTPException(
            status_code=409,
            detail="Invalid email"
        )

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

    reader = DimReader(
        full_name=format_full_name(data_in.full_name),
        email=email
    )

    session.add(reader)
    await session.commit()
    await session.refresh(reader)

    return {
        "id": reader.id,
        "full_name": reader.full_name,
        "email": reader.email
    }


# Update reader
async def update_reader(
    session: AsyncSession,
    reader_id: int,
    data_in: ReaderUpdate
):
    reader = await session.get(DimReader, reader_id)

    if not reader:
        raise HTTPException(
            status_code=404,
            detail="Reader not found"
        )

    data = data_in.model_dump(exclude_unset=True)

    # Update email
    if "email" in data:
        email = data["email"].strip().lower()

        email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"
        if not re.match(email_regex, email):
            raise HTTPException(
                status_code=409,
                detail="Invalid email"
            )

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

    await session.commit()
    await session.refresh(reader)

    return {
        "id": reader.id,
        "full_name": reader.full_name,
        "email": reader.email
    }

# Search reader
async def search_readers(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    base_stmt = select(DimReader)

    # фильтрация только если есть запрос
    if query and query.strip():
        q = query.strip().lower()

        base_stmt = base_stmt.where(
            or_(
                DimReader.full_name.ilike(f"%{q}%"),
                DimReader.email.ilike(f"%{q}%")
            )
        )

    # total count
    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.exec(total_stmt)).one()

    # pagination
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


# Delete reader
async def delete_reader(
    session: AsyncSession,
    reader_id: int
):
    reader = await session.get(DimReader, reader_id)

    if not reader:
        raise HTTPException(
            status_code=404,
            detail="Reader not found"
        )

    loans = (
        await session.exec(
            select(FactLoan).where(
                FactLoan.reader_id == reader_id
            )
        )
    ).all()

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

    if any(loan.fine_amount > 0 for loan in loans):
        raise HTTPException(
            status_code=409,
            detail="Reader has unpaid fines"
        )

    await session.delete(reader)
    await session.commit()

    return {
        "status": "deleted"
    }