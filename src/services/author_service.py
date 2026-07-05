# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel import select, or_, cast, String
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import DimAuthor, BookAuthor
# Schemas:
from schemas.author import AuthorCreate, AuthorUpdate
# ==================================================



# ==================================================
#                      functions
# ==================================================

# Normalize author's name and country
def format_author(author: DimAuthor) -> DimAuthor:
    author.name = author.name.title()

    if author.country:
        author.country = author.country.title()

    return author

# Normalize author's data
def normalize_author_data(data: dict) -> dict:
    for field in ("name", "country"):
        if data.get(field):
            data[field] = data[field].strip().lower()

    return data


# Create a new author
async def create_author(
    session: AsyncSession,
    author_data: AuthorCreate
):
    # Convert to dict
    data = normalize_author_data(author_data.model_dump())

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

    author = DimAuthor(**data)

    session.add(author)
    await session.commit()
    await session.refresh(author)

    return format_author(author)


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
    authors = result.all()

    # Format output
    return [format_author(author) for author in authors]


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

    update_data = normalize_author_data(
        author_data.model_dump(exclude_unset=True)
    )

    if "name" in update_data:
        statement = select(DimAuthor).where(
            DimAuthor.name == update_data["name"],
            DimAuthor.id != author_id
        )

        result = await session.exec(statement)
        existing = result.first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Author with this name already exists"
            )

    for key, value in update_data.items():
        setattr(author, key, value)

    await session.commit()
    await session.refresh(author)

    return format_author(author)


# Delete an author
async def delete_author(
    session: AsyncSession,
    author_id: int,
    force: bool = False
):

    author = await session.get(DimAuthor, author_id)

    if not author:
        raise HTTPException(404, "Author not found")

    # check links
    links = (await session.exec(
        select(BookAuthor).where(BookAuthor.author_id == author_id)
    )).all()

    if links and not force:
        return {
            "warning": "Author is linked to books",
            "books_count": len(links),
            "message": "Set force=True to delete author and unlink books"
        }

    # DELETE ALL LINKS IN ONE GO (better than loop)
    if links:
        await session.exec(
            select(BookAuthor).where(BookAuthor.author_id == author_id)
        )
        for link in links:
            await session.delete(link)

    # delete author
    await session.delete(author)
    await session.commit()

    return {"status": "deleted"}