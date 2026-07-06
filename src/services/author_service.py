# ==================================================
#                       imports
# ==================================================
# Libraries:
from sqlmodel import select, or_, cast, String, func
from fastapi import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import DimAuthor, BookAuthor
# Schemas:
from schemas.author import AuthorCreate, AuthorUpdate




# ==================================================
#      Service functions - helpers and CRUD
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


# Create a new author service
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

    # Execute the statement - find the author
    result = await session.exec(statement)
    existing_author = result.first()

    # If the author already exists, raise an exception
    if existing_author:
        raise HTTPException(
            status_code=409,
            detail="Author already exists"
        )

    # Create a new author
    author = DimAuthor(**data)

    # Write the author to the database
    session.add(author)
    await session.commit()
    await session.refresh(author)

    return format_author(author)


# Search for authors searched by name or country, birth year
async def search_authors(
    session: AsyncSession,
    query: str | None = None,
    limit: int = 10,
    offset: int = 0
):
    # Base query (always exists)
    stmt = select(DimAuthor)

    # Optional filtering
    if query:
        # Normalize query string
        q = query.strip().lower()

        # Ignore empty string after strip
        if q:
            # Find authors by name, country or birth year
            stmt = stmt.where(
                or_(
                    DimAuthor.name.ilike(f"%{q}%"),
                    DimAuthor.country.ilike(f"%{q}%"),
                    cast(DimAuthor.birth_year, String).ilike(f"%{q}%")
                )
            )

    # Total count (with or without filter)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.exec(count_stmt)).one()

    # Pagination
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


# Update an author by ID
async def update_author(
    session: AsyncSession,
    author_id: int,
    author_data: AuthorUpdate
):
    # Get the author by ID
    author = await session.get(DimAuthor, author_id)

    if not author:
        raise HTTPException(
            status_code=404,
            detail="Author not found"
        )

    # Normalize the data
    update_data = normalize_author_data(
        author_data.model_dump(exclude_unset=True)
    )

    # Check if the new name is unique
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

    # Update the author's attributes
    for key, value in update_data.items():
        setattr(author, key, value)

    # Commit the changes
    await session.commit()
    await session.refresh(author)

    return format_author(author)


# Delete an author by ID
async def delete_author(
    session: AsyncSession, 
    author_id: int, 
    force: bool = False
):
    # Get the author by ID
    author = await session.get(DimAuthor, author_id)

    if not author:
        raise HTTPException(404, "Author not found")

    # Check if the user wants to force deletion
    if not force:

        links = (await session.exec(
            select(BookAuthor).where(BookAuthor.author_id == author_id)
        )).first()

        # Check if the author has any book links
        if links:
            return {
                "warning": "Author is linked to books",
                "message": "Set force=True to delete author and cascade links"
            }

    # Delete the author
    await session.delete(author)
    await session.commit()

    return {"status": "deleted"}