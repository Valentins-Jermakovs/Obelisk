# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import DimLanguage, BookLanguage
# Schemas:
from schemas.language import LanguageCreate, LanguageUpdate
# =====================================================


# ===================================================
#                       functions
# ===================================================


# Create a new language in the database
async def create_language(
    session: AsyncSession,
    data_in: LanguageCreate
):
    code = data_in.code.strip().lower()
    name = data_in.name.strip().title() if data_in.name else None

    existing = (await session.exec(
        select(DimLanguage).where(DimLanguage.code == code)
    )).first()

    if existing:
        raise HTTPException(409, "Language already exists")

    language = DimLanguage(
        code=code,
        name=name
    )

    session.add(language)
    await session.commit()
    await session.refresh(language)

    return language


# Search
async def search_languages(
    session: AsyncSession,
    query: str
):
    q = query.strip().lower()

    languages = (await session.exec(
        select(DimLanguage)
        .where(
            (DimLanguage.code.ilike(f"%{q}%")) |
            (DimLanguage.name.ilike(f"%{q}%"))
        )
        .limit(10)
    )).all()

    return languages


# Update
async def update_language(
    session: AsyncSession,
    language_id: int,
    data_in: LanguageUpdate
):
    language = await session.get(DimLanguage, language_id)

    if not language:
        raise HTTPException(404, "Language not found")

    data = data_in.model_dump(exclude_unset=True)

    if "code" in data:
        code = data["code"].strip().lower()

        existing = (await session.exec(
            select(DimLanguage).where(
                DimLanguage.code == code,
                DimLanguage.id != language_id
            )
        )).first()

        if existing:
            raise HTTPException(409, "Language code already exists")

        language.code = code

    if "name" in data:
        language.name = data["name"].strip().title()

    await session.commit()
    await session.refresh(language)

    return language


# Delete
async def delete_language(
    session: AsyncSession,
    language_id: int,
    force: bool = False
):
    language = await session.get(DimLanguage, language_id)

    if not language:
        raise HTTPException(404, "Language not found")

    # check links
    linked = (await session.exec(
        select(BookLanguage).where(
            BookLanguage.language_id == language_id
        )
    )).first()

    if linked and not force:
        raise HTTPException(
            status_code=409,
            detail="Language is linked to books. Use force=true to delete anyway."
        )

    await session.delete(language)
    await session.commit()

    return {"status": "deleted"}