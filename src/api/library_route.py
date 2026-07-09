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
from utils.token_utils import admin_required, validate_token



# Router object for export
router = APIRouter(
    prefix="/libraries",
    tags=["Libraries endpoints - [create, read, update, delete]"]
)


# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create library
# Administrator role required
@router.post(
    "/", 
    response_model=LibraryRead,
    summary="Create a library, Admin required"
)
async def create_library_route(
    data: LibraryCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await create_library(
        session=session, 
        data_in=data
    )


# Search library by name, city, address
# Can access everyone
@router.get(
    "/search", 
    response_model=LibrarySearchResponse,
    summary="Search library by name, city, address, roles not required"
)
async def search_libraries_route(
    q: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await search_libraries(
        session=session,
        query=q,
        limit=limit,
        offset=offset
    )


# Get library by ID
# Can access everyone
@router.get(
    "/{library_id}", 
    response_model=LibraryRead,
    summary="Get library by ID, roles not required"
)
async def get_library_route(
    library_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await get_library(
        session=session, 
        library_id=library_id
    )


# Update library by ID
# Administrator role required
@router.patch(
    "/{library_id}", 
    response_model=LibraryRead,
    summary="Update a library, Admin required"
)
async def update_library_route(
    library_id: int,
    data: LibraryUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await update_library(
        session=session, 
        library_id=library_id, 
        data_in=data
    )


# Delete library by ID
# Administrator role required
@router.delete(
    "/{library_id}",
    response_model=Union[LibraryDeleteResponse, LibraryDeleteWarning],
    summary="Delete library by ID, set force=True to delete entities, Admin required"
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