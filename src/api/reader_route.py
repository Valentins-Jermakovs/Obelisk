# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Schemas:
from schemas.reader import (
    ReaderCreate,
    ReaderUpdate,
    ReaderRead,
    ReaderSearchResponse,
    ReaderDeleteResponse
)
# Services:
from services.reader_service import (
    create_reader,
    update_reader,
    search_readers,
    delete_reader,
)
# Utils:
from utils.token_utils import (
    admin_or_librarian_required, 
    admin_required, 
    validate_token
)



# Router object for export
router = APIRouter(
    prefix="/readers",
    tags=["Reader endpoints - [create, read, update, delete]"],
)


# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create reader
# Everyone can be a reader
# Need an email and fullname
@router.post(
    "/",
    response_model=ReaderRead,
    summary="Create a reader, no role required"
)
async def create(
    data: ReaderCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await create_reader(
        session=session, 
        data_in=data,
        payload=payload
    )


# Search readers by name or email
# Administrator or Librarian required
@router.get(
    "/search", 
    response_model=ReaderSearchResponse,
    summary="Search readers by name or email, Admin or Librarian required"
)
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


# Update reader by ID
# No role required
@router.patch(
    "/{reader_id}",
    response_model=ReaderRead,
    summary="Update a reader by ID, no role required",
)
async def update(
    reader_id: int,
    data: ReaderUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(validate_token)
):
    return await update_reader(
        session=session,
        reader_id=reader_id,
        data_in=data,
        payload=payload
    )


# Delete reader by ID
# Administrator role required
@router.delete(
    "/{reader_id}",
    response_model=ReaderDeleteResponse,
    summary="Delete reader by ID, Admin required"
)
async def delete(
    reader_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_reader(
        session=session,
        reader_id=reader_id,
        payload=payload
    )