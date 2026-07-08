# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Schemas
from schemas.genre import (
    GenreCreate, 
    GenreUpdate, 
    GenreRead, 
    GenreSearchResponse,
    GenreDeleteResponse
)
# Services
from services.genre_service import (
    create_genre,
    search_genres,
    update_genre,
    delete_genre
)
# Auth
from utils.token_utils import admin_required, admin_or_librarian_required



# Router object for export
router = APIRouter(
    prefix="/genres",
    tags=["Genres endpoints - [create, read, update, delete]"]
)


# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create genre - create a new genre
# Return a genre object
# Administrator role required
@router.post(
    "/", 
    response_model=GenreRead,
    summary="Create genre, Admin required"
)
async def create(
    data: GenreCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await create_genre(
        session=session, 
        data_in=data
    )


# Search genres - get all genres from the database
# Administrator or librarian role required
@router.get(
    "/search", 
    response_model=GenreSearchResponse,
    summary="Search genre, Admin or Librarian required"
)
async def search(
    query: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    return await search_genres(
        session=session,
        query=query,
        limit=limit,
        offset=offset
    )


# Update genre - update a genre object
# Return a genre object
# Administrator role required
@router.patch(
    "/{genre_id}",
    response_model=GenreRead,
    summary="Update genre, Admin required"
)
async def update(
    genre_id: int,
    data: GenreUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await update_genre(
        session=session, 
        genre_id=genre_id,
        data_in=data
    )


# Delete genre by id
# Administrator role required
@router.delete(
    "/{genre_id}",
    response_model=GenreDeleteResponse,
    summary="Delete genre, set force=True to delete entities, Admin required"
)
async def delete(
    genre_id: int,
    force: bool = False,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_genre(
        session=session, 
        genre_id=genre_id, 
        force=force
    )