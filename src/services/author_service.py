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
    statement = select(DimAuthor).where(
        DimAuthor.name == author_data.name
    )

    result = await session.exec(statement)
    existing_author = result.first()

    if existing_author:
        raise HTTPException(
            status_code=409,
            detail="Author already exists"
        )

    author = DimAuthor(**author_data.model_dump())

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
    author = await session.get(DimAuthor, author_id)

    if not author:
        raise HTTPException(
            status_code=404,
            detail="Author not found"
        )

    update_data = author_data.model_dump(exclude_unset=True)

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