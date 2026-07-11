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
    DimReader, 
    FactLoan, 
    LoanStatus,
    AuditAction, 
    EntityType
)
# Schemas:
from schemas.reader import ReaderCreate, ReaderUpdate
# Utils:
from utils.formatters import format_full_name
# Services:
from services.audit_service import (
    write_audit_log, 
    write_failed_audit_log
)



# ===================================================
#      Service code - create, update, get, delete
# ===================================================

# Create reader
async def create_reader(
    session: AsyncSession,
    data_in: ReaderCreate,
    payload: dict
):
    # Normalize email
    email = data_in.email.strip().lower()

    # Validate email
    email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"

    if not re.match(email_regex, email):

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.READER,
            description="Failed to create reader",
            error="Invalid email",
            full_name=format_full_name(data_in.full_name),
            email=email,
        )

        # Commit log
        await session.commit()

        # Raise exception
        raise HTTPException(
            status_code=400,
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

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.READER,
            description="Failed to create reader",
            error="Reader already exists",
            full_name=format_full_name(data_in.full_name),
            email=email,
        )

        # Commit log
        await session.commit()

        # Raise exception
        raise HTTPException(
            status_code=409,
            detail="Reader already exists"
        )


     # Validate phone
    phone_val = None

    if hasattr(data_in, "phone") and data_in.phone:

        phone_pattern = re.compile(
            r"^\+?[0-9\s\-\(\)]{7,20}$"
        )

        if not phone_pattern.match(
            data_in.phone.strip()
        ):

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.CREATE,
                entity_type=EntityType.READER,
                description="Failed to create reader",
                error="Invalid phone",
                full_name=format_full_name(data_in.full_name),
                email=email,
                phone=data_in.phone,
            )

            # Commit log
            await session.commit()

            # Raise exception
            raise HTTPException(
                status_code=400,
                detail="Invalid phone"
            )

        phone_val = data_in.phone.strip()

    # Create the new READER
    reader = DimReader(
        full_name=format_full_name(data_in.full_name),
        email=email,
        phone=phone_val,
        birth_date=(data_in.birth_date if hasattr(data_in, 'birth_date') else None)
    )

    # Add the new READER to the database
    session.add(reader)

    # Flush to get generated ID
    await session.flush()


    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.READER,
        description=f"Created reader '{reader.full_name}'",
        reader_id=reader.id,
        full_name=reader.full_name,
        email=reader.email,
        phone=reader.phone,
        birth_date=reader.birth_date,
    )

    # Commit everything
    await session.commit()

    # Refresh object
    await session.refresh(reader)

    # Return data
    return {
        "id": reader.id,
        "full_name": reader.full_name,
        "email": reader.email,
        "phone": reader.phone,
        "birth_date": reader.birth_date,
        "registered_at": reader.registered_at
    }


# Update reader by ID
async def update_reader(
    session: AsyncSession,
    reader_id: int,
    data_in: ReaderUpdate,
    payload: dict
):
    # Get the reader by ID
    reader = await session.get(DimReader, reader_id)

    if not reader:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.READER,
            description=f"Failed to update reader with id {reader_id}",
            error="Reader not found",
            reader_id=reader_id,
        )

        # Commit log
        await session.commit()

        # Raise exception
        raise HTTPException(
            status_code=404,
            detail="Reader not found"
        )


    # Save old data for audit log
    old_data = {
        "full_name": reader.full_name,
        "email": reader.email,
        "phone": reader.phone,
        "birth_date": reader.birth_date,
    }

    # Translate data to model fields
    data = data_in.model_dump(exclude_unset=True)

    # Update email
    if "email" in data:

        email = data["email"].strip().lower()

        email_regex = r"^[\w\.-]+@([\w\-]+\.)+[a-zA-Z]{2,}$"

        # Check if the email is valid
        if not re.match(email_regex, email):

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.READER,
                description=f"Failed to update reader '{reader.full_name}'",
                error="Invalid email",
                reader_id=reader.id,
                email=email,
            )

            # Commit log
            await session.commit()

            # Raise exception
            raise HTTPException(
                status_code=400,
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

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.READER,
                description=f"Failed to update reader '{reader.full_name}'",
                error="Email already in use",
                reader_id=reader.id,
                email=email,
            )

            # Commit log
            await session.commit()

            # Raise exception
            raise HTTPException(
                status_code=409,
                detail="Email already in use"
            )


        reader.email = email


    # Update full name
    if "full_name" in data:
        reader.full_name = format_full_name(data["full_name"])

    
    # Update phone
    if "phone" in data:

        if data["phone"]:

            phone_pattern = re.compile(
                r"^\+?[0-9\s\-\(\)]{7,20}$"
            )

            # Check if the phone number is valid
            if not phone_pattern.match(
                data["phone"].strip()
            ):

                # Write audit log
                await write_failed_audit_log(
                    session=session,
                    payload=payload,
                    action=AuditAction.UPDATE,
                    entity_type=EntityType.READER,
                    description=f"Failed to update reader '{reader.full_name}'",
                    error="Invalid phone",
                    reader_id=reader.id,
                    phone=data["phone"],
                )

                # Commit log
                await session.commit()

                # Raise exception
                raise HTTPException(
                    status_code=400,
                    detail="Invalid phone"
                )


            reader.phone = data["phone"].strip()

        else:
            reader.phone = None

    # Update birth_date
    if "birth_date" in data:
        reader.birth_date = data["birth_date"]


    # Flush changes
    await session.flush()


    # Save new data
    new_data = {
        "full_name": reader.full_name,
        "email": reader.email,
        "phone": reader.phone,
        "birth_date": reader.birth_date,
    }


    # Write success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.UPDATE,
        entity_type=EntityType.READER,
        description=f"Updated reader '{reader.full_name}'",
        reader_id=reader.id,
        old_data=old_data,
        new_data=new_data,
    )


    # Update READER
    await session.commit()
    await session.refresh(reader)

    return {
        "id": reader.id,
        "full_name": reader.full_name,
        "email": reader.email,
        "phone": reader.phone,
        "birth_date": reader.birth_date,
        "registered_at": reader.registered_at
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
                DimReader.email.ilike(f"%{q}%"),
                DimReader.phone.ilike(f"%{q}%")
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
                "email": r.email,
                "phone": r.phone,
                "birth_date": r.birth_date,
                "registered_at": r.registered_at
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
    reader_id: int,
    payload: dict
):
    # Get reader by ID
    reader = await session.get(DimReader, reader_id)

    if not reader:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.READER,
            description=f"Failed to delete reader with id {reader_id}",
            error="Reader not found",
            reader_id=reader_id,
        )

        # Commit log
        await session.commit()

        # Return error response
        raise HTTPException(
            status_code=404,
            detail="Reader not found"
        )


    # Get reader loans
    loans = (
        await session.exec(
            select(FactLoan).where(
                FactLoan.reader_id == reader_id
            )
        )
    ).all()


    # Check active loans
    active_loans = [
        loan for loan in loans
        if loan.status in (
            LoanStatus.ACTIVE,
            LoanStatus.OVERDUE,
            LoanStatus.LOST
        )
    ]


    # If reader has active loans, write failed audit log and return error response
    if active_loans:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.READER,
            description=f"Failed to delete reader '{reader.full_name}'",
            error="Reader has active loans",
            reader_id=reader.id,
            active_loans=len(active_loans),
        )

        # Commit log
        await session.commit()

        # Return error response
        raise HTTPException(
            status_code=409,
            detail="Reader has active loans"
        )


    # Check unpaid fines
    unpaid_fines = [
        loan for loan in loans
        if loan.fine_amount > 0
    ]

    if unpaid_fines:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.READER,
            description=f"Failed to delete reader '{reader.full_name}'",
            error="Reader has unpaid fines",
            reader_id=reader.id,
            unpaid_fines=len(unpaid_fines),
            total_fine=sum(
                loan.fine_amount
                for loan in unpaid_fines
            ),
        )

        # Commit log
        await session.commit()

        # Return error response
        raise HTTPException(
            status_code=409,
            detail="Reader has unpaid fines"
        )


    # Save old data
    old_data = {
        "id": reader.id,
        "full_name": reader.full_name,
        "email": reader.email,
        "phone": reader.phone,
        "birth_date": reader.birth_date,
        "registered_at": reader.registered_at,
    }


    # Delete reader
    await session.delete(reader)

    # Flush
    await session.flush()


    # Success audit
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.READER,
        description=f"Deleted reader '{reader.full_name}'",
        reader_id=reader.id,
        reader_name=reader.full_name,
        old_data=old_data,
    )

    # Commit to DB
    await session.commit()


    return {
        "status": "deleted"
    }