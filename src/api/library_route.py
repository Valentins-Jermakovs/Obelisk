# ==================================================
#                     imports
# ==================================================
# Libraries:
from typing import Union
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Schemas:
from schemas.library import (
    LibraryCreate,
    LibraryUpdate,
    LibraryRead,
    LibraryDeleteWarning,
    LibraryDeleteResponse,
    LibrarySearchResponse
)
# Services:
from services.library_service import (
    create_library,
    search_libraries,
    get_library,
    update_library,
    delete_library
)
# Utils:
from utils.token_utils import admin_required
# ===================================================


# Router
router = APIRouter(
    prefix="/libraries",
    tags=["Libraries"]
)


# ==================================================
#                     routes
# ==================================================

# Create
@router.post("/", response_model=LibraryRead, status_code=201)
async def create_library_route(
    data: LibraryCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await create_library(session, data)


# Search
@router.get("/search", response_model=LibrarySearchResponse)
async def search_libraries_route(
    q: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db)
):
    return await search_libraries(
        session=session,
        query=q,
        limit=limit,
        offset=offset
    )


# Get by ID
@router.get("/{library_id}", response_model=LibraryRead)
async def get_library_route(
    library_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await get_library(session, library_id)


# Update
@router.patch("/{library_id}", response_model=LibraryRead)
async def update_library_route(
    library_id: int,
    data: LibraryUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await update_library(session, library_id, data)


# Delete
@router.delete(
    "/{library_id}",
    response_model=Union[LibraryDeleteResponse, LibraryDeleteWarning]
)
async def delete_library_route(
    library_id: int,
    force: bool = False,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_library(
        session=session,
        library_id=library_id,
        force=force
    )