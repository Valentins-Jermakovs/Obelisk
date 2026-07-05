# ==================================================
#                     imports
# ==================================================
# Libraries:
from typing import Union
from fastapi import APIRouter, Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from config.db_dependency import get_db
from schemas.author import (
    AuthorCreate,
    AuthorUpdate,
    AuthorRead,
    AuthorDeleteResponse,
    AuthorDeleteWarning
)
# Services:
from services.author_service import (
    create_author,
    search_authors,
    update_author,
    delete_author
)
# Utils:
from utils.token_utils import admin_required, admin_or_librarian_required
# ==================================================


# Router
router = APIRouter(
    prefix="/authors",
    tags=["Authors"]
)


# ==================================================
#                     routes
# ==================================================

# Create author
@router.post("/", response_model=AuthorRead, status_code=201)
async def create_author_route(
    author: AuthorCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await create_author(session, author)


# Search author
@router.get("/search", response_model=list[AuthorRead])
async def search_authors_route(
    q: str,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    return await search_authors(session, q)

# Update author
@router.patch(
    "/{author_id}",
    response_model=AuthorRead
)
async def update_author_route(
    author_id: int,
    author: AuthorUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await update_author(
        session=session,
        author_id=author_id,
        author_data=author
    )


# Delete author
@router.delete(
    "/{author_id}",
    response_model=Union[AuthorDeleteResponse, AuthorDeleteWarning]
)
async def delete_author_route(
    author_id: int,
    force: bool = False,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_author(
        session=session,
        author_id=author_id,
        force=force
    )