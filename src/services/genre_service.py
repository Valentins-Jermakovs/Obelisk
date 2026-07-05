# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import re
# Models:
from models import DimGenre, BookGenre
# Schemas:
from schemas.genre import GenreCreate, GenreUpdate
# =====================================================

# ===================================================
#                       functions
# ===================================================

# Create a new genre
async def create_genre(
    session: AsyncSession,
    data_in: GenreCreate
):
    name = data_in.name.strip().title()

    existing = (
        await session.exec(
            select(DimGenre).where(DimGenre.name == name)
        )
    ).first()

    if existing:
        raise HTTPException(
            409,
            "Genre already exists"
        )

    genre = DimGenre(name=name)

    session.add(genre)
    await session.commit()
    await session.refresh(genre)

    return genre


# Search genres
async def search_genres(
    session: AsyncSession,
    query: str
):
    q = query.strip().lower()

    genres = (
        await session.exec(
            select(DimGenre)
            .where(
                DimGenre.name.ilike(f"%{q}%")
            )
            .limit(10)
        )
    ).all()

    return genres


# Update genres
async def update_genre(
    session: AsyncSession,
    genre_id: int,
    data_in: GenreUpdate
):
    genre = await session.get(DimGenre, genre_id)

    if not genre:
        raise HTTPException(
            404,
            "Genre not found"
        )

    if data_in.name is not None:

        name = data_in.name.strip().title()

        existing = (
            await session.exec(
                select(DimGenre).where(
                    DimGenre.name == name,
                    DimGenre.id != genre_id
                )
            )
        ).first()

        if existing:
            raise HTTPException(
                409,
                "Genre already exists"
            )

        genre.name = name

    await session.commit()
    await session.refresh(genre)

    return genre


# Delete genres
async def delete_genre(
    session: AsyncSession,
    genre_id: int,
    force: bool = False
):
    genre = await session.get(DimGenre, genre_id)

    if not genre:
        raise HTTPException(
            status_code=404,
            detail="Genre not found"
        )

    # Check for linked books
    linked = (
        await session.exec(
            select(BookGenre).where(
                BookGenre.genre_id == genre_id
            )
        )
    ).first()

    if linked and not force:
        raise HTTPException(
            status_code=409,
            detail=(
                "Genre is assigned to one or more books. "
                "Use force=true to delete it together with all associations."
            )
        )

    await session.delete(genre)
    await session.commit()

    return {
        "status": "deleted"
    }