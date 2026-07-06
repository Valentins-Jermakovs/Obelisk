# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select, or_, func
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import DimLanguage, BookLanguage
# Schemas:
from schemas.language import LanguageCreate, LanguageUpdate



# ===================================================
#      Service code - create, update, get, delete
# ===================================================


# Create a new language in the database
async def create_language(
    session: AsyncSession,
    data_in: LanguageCreate
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
        raise HTTPException(409, "Language already exists")

    # Create a new LANGUAGE
    language = DimLanguage(
        code=code,
        name=name
    )

    # Write the new LANGUAGE to the database
    session.add(language)
    await session.commit()
    await session.refresh(language)

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
        "returned": len(languages)
    }


# Update a language service
async def update_language(
    session: AsyncSession,
    language_id: int,
    data_in: LanguageUpdate
):
    # Get the language
    language = await session.get(DimLanguage, language_id)

    # If the language does not exist, raise an exception
    if not language:
        raise HTTPException(404, "Language not found")

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
            raise HTTPException(409, "Language code already exists")

        language.code = code

    # If the name is provided, update it
    if "name" in data:
        language.name = data["name"].strip().title()

    # Commit changes
    await session.commit()
    await session.refresh(language)

    return language


# Delete the language by ID
async def delete_language(
    session: AsyncSession,
    language_id: int,
    force: bool = False
):
    # Get the language by ID
    language = await session.get(DimLanguage, language_id)

    # If the language does not exist, raise an exception
    if not language:
        raise HTTPException(404, "Language not found")

    # Check links
    linked = (await session.exec(
        select(BookLanguage).where(
            BookLanguage.language_id == language_id
        )
    )).first()

    # If the language has links, check if force is set
    if linked and not force:
        raise HTTPException(
            status_code=409,
            detail="Language is linked to books. Use force=true to delete anyway."
        )

    # Delete the language
    await session.delete(language)
    await session.commit()

    return {"status": "deleted"}