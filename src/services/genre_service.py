# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import DimGenre, BookGenre
# Schemas:
from schemas.genre import GenreCreate, GenreUpdate



# ===================================================
#      Service code - create, update, get, delete
# ===================================================

# Create a new genre ervice
async def create_genre(
    session: AsyncSession,
    data_in: GenreCreate
):
    # Normalize the name of the GENRE to UPPERCASE and STRIP whitespace
    name = data_in.name.strip().title()

    # Try to find an existing GENTE
    existing = (
        await session.exec(
            select(DimGenre).where(DimGenre.name == name)
        )
    ).first()

    # If the genre already exists, raise an exception
    if existing:
        raise HTTPException(
            409,
            "Genre already exists"
        )

    # Create a new genre
    genre = DimGenre(name=name)

    # Write the new genre to the database
    session.add(genre)
    await session.commit()
    await session.refresh(genre)

    return genre


# Search genres by name
async def search_genres(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # Create a query statement
    base_stmt = select(DimGenre)

    # Filter by name
    if query and query.strip():
        q = query.strip().lower()

        base_stmt = base_stmt.where(
            DimGenre.name.ilike(f"%{q}%")
        )

    # Total
    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await session.exec(total_stmt)).one()

    # Pagination
    stmt = base_stmt.offset(offset).limit(limit)
    result = await session.exec(stmt)
    genres = result.all()

    return {
        "items": [
            {"id": g.id, "name": g.name}
            for g in genres
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(genres)
    }


# Update genres by id
async def update_genre(
    session: AsyncSession,
    genre_id: int,
    data_in: GenreUpdate
):
    # Check for existence
    genre = await session.get(DimGenre, genre_id)

    # Heck for existence
    if not genre:
        raise HTTPException(
            404,
            "Genre not found"
        )

    # Update data
    if data_in.name is not None:

        # Normalize the input
        name = data_in.name.strip().title()

        # Get existing
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

        # Update the name
        genre.name = name

    # Commit changes
    await session.commit()
    await session.refresh(genre)

    return genre


# Delete genres by ID
async def delete_genre(
    session: AsyncSession,
    genre_id: int,
    force: bool = False
):
    # Get genre
    genre = await session.get(DimGenre, genre_id)

    # Check for existence
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

    # Check for linked books
    if linked and not force:
        raise HTTPException(
            status_code=409,
            detail=(
                "Genre is assigned to one or more books. "
                "Use force=true to delete it together with all associations."
            )
        )

    # Delete genre
    await session.delete(genre)
    await session.commit()

    return {
        "status": "deleted"
    }