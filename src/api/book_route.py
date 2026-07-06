# ==================================================
#                     imports
# ==================================================
from typing import Union
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from config.db_dependency import get_db
from schemas.book import (
    BookCreate,
    BookUpdate,
    BookRead,
    BookSearchResponse,
    BookDeleteResponse,
    BookDeleteWarning
)
# Services:
from services.book.book_service import (
    create_book,
    search_books,
    update_book,
    delete_book,
    get_book
)
# Utils:
from utils.token_utils import admin_required, admin_or_librarian_required
# ==================================================


# Router
router = APIRouter(
    prefix="/books",
    tags=["Books"]
)


# ==================================================
#                     routes
# ==================================================

# Create book
@router.post("/", response_model=BookRead, status_code=201)
async def create_book_route(
    book: BookCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    book_obj = await create_book(session, book, payload)
    return await get_book(session, book_obj.id)


# Search books
@router.get("/search", response_model=BookSearchResponse)
async def search_books_route(
    q: str | None = None,
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    return await search_books(
        session=session,
        query=q,
        limit=limit,
        offset=offset
    )


# Get book
@router.get("/{book_id}", response_model=BookRead)
async def get_book_route(
    book_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    return await get_book(session, book_id)


# Update book
@router.patch(
    "/{book_id}",
    response_model=BookRead
)
async def update_book_route(
    book_id: int,
    book: BookUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    await update_book(
        session=session,
        book_id=book_id,
        data=book,
        payload=payload
    )
    return await get_book(session, book_id)


# Delete book
@router.delete(
    "/{book_id}",
    response_model=Union[BookDeleteResponse, BookDeleteWarning]
)
async def delete_book_route(
    book_id: int,
    force: bool = False,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    return await delete_book(
        session=session,
        book_id=book_id,
        force=force,
        payload=payload
    )
