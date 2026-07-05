# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel import select, or_, cast, String
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
# Models:
from models import DimAuthor, BookAuthor
# Schemas:
from schemas.author import AuthorCreate, AuthorUpdate
# ==================================================



# ==================================================
#                      functions
# ==================================================

# Create a new author
async def create_author(
    session: AsyncSession,
    author_data: AuthorCreate
):
    # Convert to dict
    data = author_data.model_dump()

    # Normalize data
    data["name"] = data["name"].strip().lower()
    data["country"] = (
        data["country"].strip().lower()
        if data["country"] is not None
        else None
    )

    # Check if the author already exists
    statement = select(DimAuthor).where(
        DimAuthor.name == data["name"]
    )

    result = await session.exec(statement)
    existing_author = result.first()

    if existing_author:
        raise HTTPException(
            status_code=409,
            detail="Author already exists"
        )

    # Create author
    author = DimAuthor(**data)

    # Save to database
    session.add(author)
    await session.commit()
    await session.refresh(author)

    return author


# Search for authors
async def search_authors(
    session: AsyncSession,
    query: str
):
    q = query.lower().strip()

    statement = select(DimAuthor).where(
        or_(
            DimAuthor.name.ilike(f"%{q}%"),
            DimAuthor.country.ilike(f"%{q}%"),
            cast(DimAuthor.birth_year, String).ilike(f"%{q}%")
        )
    ).limit(10)

    result = await session.exec(statement)
    return result.all()


# Update an author
async def update_author(
    session: AsyncSession,
    author_id: int,
    author_data: AuthorUpdate
):
    # Check if author exists
    author = await session.get(DimAuthor, author_id)

    if not author:
        raise HTTPException(
            status_code=404,
            detail="Author not found"
        )

    # Get only provided fields
    update_data = author_data.model_dump(exclude_unset=True)

    # Normalize string fields
    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = update_data["name"].strip().lower()

    if "country" in update_data and update_data["country"] is not None:
        update_data["country"] = update_data["country"].strip().lower()

    # Update only provided fields
    for key, value in update_data.items():
        setattr(author, key, value)

    await session.commit()
    await session.refresh(author)

    return author


# Delete an author
async def delete_author(
    session: AsyncSession, 
    author_id: int, 
    force: bool = False
):
    author = await session.get(DimAuthor, author_id)

    if not author:
        raise HTTPException(404, "Author not found")

    result = await session.exec(
        select(BookAuthor).where(BookAuthor.author_id == author_id)
    )
    links = result.all()

    if links and not force:
        return {
            "warning": "Author is linked to books",
            "books_count": len(links),
            "message": "Set force=True to delete author and unlink books"
        }

    for link in links:
        await session.delete(link)

    await session.delete(author)
    await session.commit()

    return {"status": "deleted"}