# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Database:
from config.db_dependency import get_db
# Schemas:
from schemas.reader import (
    ReaderCreate,
    ReaderUpdate,
    ReaderRead,
    ReaderSearchResponse
)
# Services:
from services.reader_service import (
    create_reader,
    update_reader,
    search_readers,
    delete_reader,
)
# Utils:
from utils.token_utils import admin_or_librarian_required, admin_required
# =====================================================


# =====================================================
#                       Router
# =====================================================
router = APIRouter(
    prefix="/readers",
    tags=["Reader services"],
)


# =====================================================
#                       Endpoints
# =====================================================

# Create reader
@router.post(
    "",
    response_model=ReaderRead
)
async def create(
    data: ReaderCreate,
    session: AsyncSession = Depends(get_db),
):
    return await create_reader(session, data)


# Search readers
@router.get("/search", response_model=ReaderSearchResponse)
async def search(
    query: str | None = None,
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    return await search_readers(
        session=session,
        query=query,
        limit=limit,
        offset=offset
    )


# Update reader
@router.patch(
    "/{reader_id}",
    response_model=ReaderRead
)
async def update(
    reader_id: int,
    data: ReaderUpdate,
    session: AsyncSession = Depends(get_db),
):
    return await update_reader(
        session,
        reader_id,
        data
    )


# Delete reader
@router.delete(
    "/{reader_id}"
)
async def delete(
    reader_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_reader(
        session,
        reader_id
    )