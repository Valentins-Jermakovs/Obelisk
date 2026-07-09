# ===================================================
#                       imports
# ===================================================
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
    LibrarianSearchResponse,
    LibrarianRead,
    LibrarianLibraryLinkResponse,
    LibrarianLibraryUnlinkResponse,
    LibrarianDeleteResponse
)
# Utils:
from utils.token_utils import admin_required, validate_token



# Router object for export
router = APIRouter(
    prefix="/librarians",
    tags=["Librarians endpoints - [create, read, update, delete]"]
)


# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create librarian
# Return a librarian object
# Everyone can be accessed to this route - Mostly automatically
@router.post(
    "/",
    response_model=LibrarianRead,
    summary="Create librarian, no role required"
)
async def create(
    data: LibrarianCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await create_librarian(
        session=session, 
        data_in=data
    )


# Update librarian
# Everyone can be accessed to this route - Mostly automatically
@router.patch(
    "/{librarian_id}",
    response_model=LibrarianRead,
    summary="Update librarian, no role required"
)
async def update(
    librarian_id: int,
    data: LibrarianUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await update_librarian(
        session=session, 
        librarian_id=librarian_id, 
        data_in=data
    )

# Link library with librarian
# Administrator role required
@router.post(
    "/{librarian_id}/libraries/{library_id}",
    response_model=LibrarianLibraryLinkResponse,
    summary="Update librarian, Admin role required"
)
async def link_library(
    librarian_id: int,
    library_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await add_librarian_to_library(
        session=session, 
        librarian_id=librarian_id, 
        library_id=library_id
    )


# Search librarian by name or email
# Administrator role required
@router.get(
    "/search", 
    response_model=LibrarianSearchResponse,
    summary="Search librarian, Admin role required"
)
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


# Unlink library and librarian
# Administrator role required
@router.delete(
    "/{librarian_id}/libraries/{library_id}",
    response_model=LibrarianLibraryUnlinkResponse,
    summary="Delete link between library and librarian, Admin role required"
)
async def unlink_library(
    librarian_id: int,
    library_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await remove_librarian_from_library(
        session=session, 
        librarian_id=librarian_id, 
        library_id=library_id
    )


# Delete librarian by ID
# Administrator role required
@router.delete(
    "/{librarian_id}",
    response_model=LibrarianDeleteResponse,
    summary="Delete librarian by ID, set force=True to delete entities, Admin required"
)
async def delete(
    librarian_id: int,
    force: bool = False,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_librarian(
        session=session, 
        librarian_id=librarian_id,
        force=force
    )