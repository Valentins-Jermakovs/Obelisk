# =====================================================
#                        Imports
# =====================================================

# Libraries:
from fastapi import HTTPException
from sqlmodel import select, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession

# Models:
from models import (
    DimLanguage, 
    BookLanguage,
    AuditAction, 
    EntityType
)

# Schemas:
from schemas import LanguageCreate, LanguageUpdate

# Services:
from services.audit_service import (
    write_audit_log, 
    write_failed_audit_log
)



# =====================================================
#                     Services
# =====================================================

# Create a new language in the database
async def create_language(
    session: AsyncSession,
    data_in: LanguageCreate,
    payload: dict
):
    # Normalize the code and name of the LANGUAGE to UPPERCASE and STRIP whitespace
    code = data_in.code.strip().lower()
    name = data_in.name.strip().title() if data_in.name else None

    # Try to find an existing LANGUAGE
    existing = (await session.exec(
        select(DimLanguage).where(DimLanguage.code == code)
    )).first()

    # If the LANGUAGE already exists, raise an exception
    if existing:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.CREATE,
            entity_type=EntityType.LANGUAGE, 
            description="Failed to create language",
            error="Language already exists",
            name=name,
            code=code
        )

        # Commit the transaction
        await session.commit()

        # Raise an error
        raise HTTPException(
            status_code=409, 
            detail="Language already exists"
        )

    # Create a new LANGUAGE
    language = DimLanguage(
        code=code,
        name=name
    )

    # Write the new LANGUAGE to the database
    session.add(language)

    # Flush the changes to the database
    await session.flush()

    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.CREATE,
        entity_type=EntityType.LANGUAGE, 
        description=f"Created language '{language.name.title()}'",
        language_id=language.id,
        code=language.code
    )

    # Commit the transaction
    await session.commit()

    # Refresh the new language
    await session.refresh(language)

    # Return object
    return language



# Search languages by code or name
async def search_languages(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # Create a query statement
    base_stmt = select(DimLanguage)

    # Filter by code or name
    if query and query.strip():
        q = query.strip().lower()

        base_stmt = base_stmt.where(
            or_(
                DimLanguage.code.ilike(f"%{q}%"),
                DimLanguage.name.ilike(f"%{q}%")
            )
        )

    # Total
    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.exec(total_stmt)).one()

    # Pagination
    stmt = base_stmt.offset(offset).limit(limit)
    result = await session.exec(stmt)
    languages = result.all()
    has_more = offset + len(languages) < total

    return {
        "items": [
            {
                "id": l.id,
                "code": l.code,
                "name": l.name
            }
            for l in languages
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": has_more
    }



# Update a language service
async def update_language(
    session: AsyncSession,
    language_id: int,
    data_in: LanguageUpdate,
    payload: dict
):
    # Get the language
    language = await session.get(DimLanguage, language_id)

    # If the language does not exist, raise an exception
    if not language:

        # Write an audit log for this action
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.UPDATE,
            entity_type=EntityType.LANGUAGE,
            description=f"Failed to update language with id {language_id}",
            error="Language not found",
            language_id=language_id,
        )

        # Commit the transaction
        await session.commit()

        # Raise a 404 error
        raise HTTPException(
            status_code=404, 
            detail="Language not found"
        )

    # Translate the data to a dictionary
    data = data_in.model_dump(exclude_unset=True)

    # If the code is provided, check if it already exists
    if "code" in data:
        # Normalize the code of the LANGUAGE to UPPERCASE and STRIP whitespace
        code = data["code"].strip().lower()

        # If the code already exists, raise an exception
        existing = (await session.exec(
            select(DimLanguage).where(
                DimLanguage.code == code,
                DimLanguage.id != language_id
            )
        )).first()

        if existing:

            # Write failed audit log
            await write_failed_audit_log(
                session=session,
                payload=payload,
                action=AuditAction.UPDATE,
                entity_type=EntityType.LANGUAGE,
                description="Failed to update language",
                error="Language with this code already exists",
                language_id=existing.id,
                language_code=data["code"],
                language_name=data["name"]
            )

            # Commit the transaction
            await session.commit()

            # Raise an error
            raise HTTPException(
                status_code=409, 
                detail="Language code already exists"
            )

        # Save old data for audit
        old_data = {
            "code": language.code,
            "name": language.name,
        }

        # Update the language in the database
        language.code = code

    

    # If the name is provided, update it
    if "name" in data:
        language.name = data["name"].strip().title()


    # Flush changes before audit
    await session.flush()


    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.UPDATE,
        entity_type=EntityType.LANGUAGE,
        description=f"Updated language '{language.name.title()}'",
        language_id=language.id,
        old_data=old_data,
        new_data=data
    )

    # Commit changes
    await session.commit()

    # Refresh the object
    await session.refresh(language)

    # Return object
    return language



# Delete the language by ID
async def delete_language(
    session: AsyncSession,
    language_id: int,
    payload: dict,
    force: bool = False
):
    # Get the language by ID
    language = await session.get(DimLanguage, language_id)

    # If the language does not exist, raise an exception
    if not language:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.LANGUAGE,
            description=f"Failed to delete language with id {language_id}",
            error="Language not found",
            language_id=language_id,
        )

        # Commit the transaction
        await session.commit()

        # Return error
        raise HTTPException(
            status_code=404, 
            detail="Language not found"
        )

    # Check links
    linked = (await session.exec(
        select(BookLanguage).where(
            BookLanguage.language_id == language_id
        )
    )).first()

    # If the language has links, check if force is set
    if linked and not force:

        # Write failed audit log
        await write_failed_audit_log(
            session=session,
            payload=payload,
            action=AuditAction.DELETE,
            entity_type=EntityType.LANGUAGE,
            description=f"Failed to delete language '{language.name.title()}'",
            error="Language is linked to books",
            language_id=language_id,
            force=force,
        )

        # Commit the transaction
        await session.commit()

        # Return error
        raise HTTPException(
            status_code=409,
            detail="Language is linked to books. Use force=true to delete anyway."
        )
    
    # Save data before deleting it
    language_name = language.name.title()
    language_code = language.code.lower()

    # Delete the language
    await session.delete(language)

    # Write audit log
    await write_audit_log(
        session=session,
        payload=payload,
        action=AuditAction.DELETE,
        entity_type=EntityType.LANGUAGE,
        description=f"Deleted language '{language_name}'",
        language_id=language_id,
        language_name=language_name,
        language_code=language_code,
        force=force,
    )

    # Commit the transition
    await session.commit()

    # Return response
    return {
        "status": "deleted"
    }