# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Database:
from config.db_dependency import get_db
# Utils:
from utils.token_utils import validate_token
# Schemas:
from schemas.shelf import ShelfCreate, ShelfUpdate, ShelfRead
# Services:
from services.shelf_service import (
    create_shelf,
    update_shelf,
    delete_shelf,
    search_shelves
)
# =====================================================


# =====================================================
#                       Router
# =====================================================
router = APIRouter(
    prefix="/shelves", 
    tags=["Shelves"]
)


# =====================================================
#                       Endpoints
# =====================================================

# Create
@router.post("", response_model=ShelfRead)
async def create(
    data: ShelfCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await create_shelf(
        session,
        data.library_id,
        data.code,
        data.section,
        payload
    )


# Search
@router.get("", response_model=list[ShelfRead])
async def search(
    library_id: int,
    q: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await search_shelves(session, library_id, q, payload)


# Update
@router.patch("/{shelf_id}", response_model=ShelfRead)
async def update(
    shelf_id: int,
    data: ShelfUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await update_shelf(
        session,
        shelf_id,
        data.code,
        data.section,
        payload
    )


# Delete
@router.delete("/{shelf_id}")
async def delete(
    shelf_id: int,
    force: bool = Query(False),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await delete_shelf(
        session,
        shelf_id,
        force,
        payload
    )