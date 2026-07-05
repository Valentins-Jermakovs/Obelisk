# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# DB:
from config.db_dependency import get_db
# Schemas
from schemas.genre import GenreCreate, GenreUpdate, GenreRead, GenreSearchResponse
# Services
from services.genre_service import (
    create_genre,
    search_genres,
    update_genre,
    delete_genre
)
# Auth
from utils.token_utils import admin_required, admin_or_librarian_required
# =====================================================


# =====================================================
#                       Router
# =====================================================
router = APIRouter(
    prefix="/genres",
    tags=["Genres"]
)


# =====================================================
#                       Endpoints
# =====================================================

# Create genre
@router.post(
    "",
    response_model=GenreRead
)
async def create(
    data: GenreCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await create_genre(session, data)


# Search genres
@router.get("/search", response_model=GenreSearchResponse)
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


# Update genre
@router.patch(
    "/{genre_id}",
    response_model=GenreRead
)
async def update(
    genre_id: int,
    data: GenreUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await update_genre(session, genre_id, data)


# Delete genre
@router.delete("/{genre_id}")
async def delete(
    genre_id: int,
    force: bool = False,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_genre(session, genre_id, force)