# ===================================================
#                       imports
# ===================================================
# Libraries:
from typing import Union
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Schemas:
from schemas.author import (
    AuthorCreate,
    AuthorUpdate,
    AuthorRead,
    AuthorDeleteResponse,
    AuthorDeleteWarning,
    AuthorSearchResponse
)
# Services:
from services.author_service import (
    create_author,
    search_authors,
    update_author,
    delete_author
)
# Utils:
from utils.token_utils import (
    admin_required, 
    admin_or_librarian_required
)



# Router object for export
router = APIRouter(
    prefix="/authors",
    tags=["Authors endpoints - [create, read, update, delete]"]
)


# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create author - create a new author
# Return id, name, city, birth_year
# Administrator role required
@router.post(
    "/", 
    response_model=AuthorRead,
    summary="Create author, Admin required"
)
async def create_author_route(
    author: AuthorCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await create_author(
        session=session, 
        author_data=author
    )


# Search author - search for authors by name or country, birth_year
# Return list of authors with meta data about pagination
# Administrator or librarian role required
@router.get(
    "/search", 
    response_model=AuthorSearchResponse, 
    summary="Search author, Admin or Librarian required"
)
async def search_authors_route(
    q: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    return await search_authors(
        session=session,
        query=q,
        limit=limit,
        offset=offset
    )


# Update author - update an existing author by id
# Return updated author
# Administrator role required
@router.patch(
    "/{author_id}",
    response_model=AuthorRead,
    summary="Update author, Admin required"
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


# Delete author - delete an existing author by id
# Return message or warning, use force=True, 
# to delete the author with entities (CASCADE)
# Administrator role required
@router.delete(
    "/{author_id}",
    response_model=Union[AuthorDeleteResponse, AuthorDeleteWarning],
    summary="Delete author, set force=True to delete entities, Admin required"
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