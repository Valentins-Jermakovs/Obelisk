# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Services:
from services.librarian_service import (
    create_librarian,
    update_librarian,
    add_librarian_to_library,
    search_librarians_with_libraries,
    remove_librarian_from_library,
    delete_librarian
)
# Schemas:
from schemas.librarian import (
    LibrarianCreate,
    LibrarianUpdate,
    LibrarianWithLibraries,
    LibrarianSearchResponse
)
# Utils:
from utils.token_utils import admin_required
# =====================================================


# Router
router = APIRouter(
    prefix="/librarians",
    tags=["Librarians"]
)


# ==================================================
#                     routes
# ==================================================

# Create
@router.post("")
async def create(
    data: LibrarianCreate,
    session: AsyncSession = Depends(get_db)
):
    return await create_librarian(session, data)


# Update
@router.patch("/{librarian_id}")
async def update(
    librarian_id: int,
    data: LibrarianUpdate,
    session: AsyncSession = Depends(get_db)
):
    return await update_librarian(session, librarian_id, data)

# Link library
@router.post("/{librarian_id}/libraries/{library_id}")
async def link_library(
    librarian_id: int,
    library_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await add_librarian_to_library(session, librarian_id, library_id)


# Search
@router.get("/search", response_model=LibrarianSearchResponse)
async def search(
    query: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await search_librarians_with_libraries(
        session=session,
        query=query,
        limit=limit,
        offset=offset
    )


# Unlink library
@router.delete("/{librarian_id}/libraries/{library_id}")
async def unlink_library(
    librarian_id: int,
    library_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await remove_librarian_from_library(session, librarian_id, library_id)


# Delete librarian
@router.delete("/{librarian_id}")
async def delete(
    librarian_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_librarian(session, librarian_id)