# ===================================================
#                       imports
# ===================================================
# Libraries:
from typing import Union
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Schemas:
from schemas.book import (
    BookCreate,
    BookUpdate,
    BookRead,
    BookSearchResponse,
    BookDeleteResponse,
    BookDeleteWarning
)
# Services:
from services.book_service import (
    create_book,
    search_books,
    update_book,
    delete_book,
    get_book
)
# Utils:
from utils.token_utils import (
    admin_or_librarian_required,
    validate_token
)


# Router object for export
router = APIRouter(
    prefix="/books",
    tags=["Books endpoint - [create, read, update, delete]"]
)


# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create book - create a new book
# Return a book object
# Administrator or librarian role required
@router.post(
    "/", 
    response_model=BookRead,
    summary="Create book, Admin or Librarian required"
)
async def create_book_route(
    book: BookCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    book_obj = await create_book(session, book, payload)
    return await get_book(session, book_obj.id)


# Search books - search books by title or author name
# Return a list of books objects with meta data
# Can access everyone
@router.get(
    "/search", 
    response_model=BookSearchResponse,
    summary="Search book by title, ISBN, or annotation, roles not required"
)
async def search_books_route(
    q: str | None = None,
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await search_books(
        session=session,
        query=q,
        limit=limit,
        offset=offset
    )


# Get book by ID - get a book object with meta data
# Can access everyone
@router.get(
    "/{book_id}", 
    response_model=BookRead,
    summary="Search book by ID, roles not required"
)
async def get_book_route(
    book_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await get_book(session, book_id)


# Update book - update a book object with meta data
# Return a book object with meta data
# Administrator or librarian role required
@router.patch(
    "/{book_id}", 
    response_model=BookRead,
    summary="Update book, Admin or Librarian required"
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


# Delete book - delete a book object with meta data
# Return a message or warning
# Use the `force` parameter to bypass the confirmation prompt
# Administrator or librarian role required
@router.delete(
    "/{book_id}",
    response_model=Union[BookDeleteResponse, BookDeleteWarning],
    summary="Delete book, set force=True to delete entities, Admin or Librarian required"
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
