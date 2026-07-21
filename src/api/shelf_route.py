# =====================================================
#                        Imports
# =====================================================

# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession

# Dependencies:
from config.db_dependency import get_db

# Utils:
from utils.token_utils import (
    validate_token, 
    librarian_required
)

# Schemas:
from schemas import (
    ShelfCreate, 
    ShelfUpdate, 
    ShelfRead, 
    ShelfSearchResponse,
    ShelfDeleteResponse
)

# Services:
from services.shelf_service import (
    create_shelf,
    update_shelf,
    delete_shelf,
    search_shelves
)



# Router object for export
router = APIRouter(
    prefix="/shelves", 
    tags=["Shelves endpoints - [create, read, update, delete]"]
)



# =====================================================
#                       Endpoints
# =====================================================

# Create a shelf in library
# Librarian role required
@router.post(
    "/", 
    response_model=ShelfRead,
    summary="Create a shelf, Librarian required"
)
async def create(
    data: ShelfCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)
) -> ShelfRead:
    
    # Create shelf in library
    return await create_shelf(
        session=session,
        library_id=data.library_id,
        code=data.code,
        section=data.section,
        payload=payload
    )



# Search shelves in library
# Can access to all users
@router.get(
    "/search", 
    response_model=ShelfSearchResponse,
    summary="Search shelves in library by library ID and other parameters, roles not required"
)
async def search(
    library_id: int,
    q: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
) -> ShelfSearchResponse:
    
    return await search_shelves(
        session=session,
        library_id=library_id,
        query=q,
        limit=limit,
        offset=offset
    )



# Update a shelf in library
# Librarian role required
@router.patch(
    "/{shelf_id}", 
    response_model=ShelfRead,
    summary="Update a shelf in library by ID, Librarian required"
)
async def update(
    shelf_id: int,
    data: ShelfUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)
) -> ShelfRead:
    
    # Update shelf
    return await update_shelf(
        session=session,
        shelf_id=shelf_id,
        code=data.code,
        section=data.section,
        payload=payload
    )



# Delete shelf by ID
# Librarian role required
@router.delete(
    "/{shelf_id}",
    response_model=ShelfDeleteResponse,
    summary="Delete shelf by ID, set force=True to delete entities, Admin required"
)
async def delete(
    shelf_id: int,
    force: bool = Query(False),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
) -> ShelfDeleteResponse:
    
    return await delete_shelf(
        session=session,
        shelf_id=shelf_id,
        force=force,
        payload=payload
    )