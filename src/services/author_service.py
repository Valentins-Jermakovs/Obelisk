# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel import select, or_, cast, String
from sqlalchemy import func
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
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # base query (always exists)
    stmt = select(DimAuthor)

    # optional filtering
    if query:
        q = query.strip().lower()

        if q:  # ignore empty string after strip
            stmt = stmt.where(
                or_(
                    DimAuthor.name.ilike(f"%{q}%"),
                    DimAuthor.country.ilike(f"%{q}%"),
                    cast(DimAuthor.birth_year, String).ilike(f"%{q}%")
                )
            )

    # total count (with or without filter)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.exec(count_stmt)).one()

    # pagination
    stmt = stmt.offset(offset).limit(limit)
    result = await session.exec(stmt)
    authors = result.all()

    return {
        "items": [format_author(a) for a in authors],
        "total": total,
        "limit": limit,
        "offset": offset,
        "returned": len(authors)
    }


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

    if not force:

        links = (await session.exec(
            select(BookAuthor).where(BookAuthor.author_id == author_id)
        )).first()

        if links:
            return {
                "warning": "Author is linked to books",
                "message": "Set force=True to delete author and cascade links"
            }

    await session.delete(author)
    await session.commit()

    return {"status": "deleted"}