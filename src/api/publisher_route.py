# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Utils:
from utils.token_utils import admin_required, admin_or_librarian_required
# Schemas:
from schemas.publisher import (
    PublisherCreate,
    PublisherUpdate,
    PublisherRead,
    PublisherListResponse,
    PublisherDeleteResponse
)
# Services:
from services.publisher_service import (
    create_publisher,
    update_publisher,
    delete_publisher,
    get_publisher,
    search_publishers
)


# Router object for export
router = APIRouter(
    prefix="/publishers",
    tags=["Publisher endpoints - [create, read, update, delete]"]
)


# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create publisher
# Admin role required
@router.post(
    "/",
    response_model=PublisherRead,
    summary="Create publisher, Admin role required",
)
async def create_publisher_route(
    data: PublisherCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):

    publisher = await create_publisher(
        session=session,
        name=data.name,
        country=data.country,
        payload=payload
    )

    return publisher


# Search publishers
# Admin or librarian role required
@router.get(
    "/search",
    response_model=PublisherListResponse,
    summary="Search publishers with pagination, Admin or librarian  role required",
)
async def search_publishers_route(
    query: str | None = Query(
        default=None,
        description="Search by publisher name or country"
    ),

    country: str | None = Query(
        default=None,
        description="Filter by country"
    ),

    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of records"
    ),

    offset: int = Query(
        default=0,
        ge=0,
        description="Pagination offset"
    ),

    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):

    result = await search_publishers(
        session=session,
        query=query,
        country=country,
        limit=limit,
        offset=offset
    )

    return result


# Get publisher by ID
# Librarian or admin role required
@router.get(
    "/{publisher_id}",
    response_model=PublisherRead,
    summary="Get publisher by ID, librarian or admin role required"
)
async def get_publisher_route(
    publisher_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):

    publisher = await get_publisher(
        session=session,
        publisher_id=publisher_id
    )

    return publisher


# Update publisher
# Admin role required
@router.patch(
    "/{publisher_id}",
    response_model=PublisherRead,
    summary="Update publisher, Admin role required"
)
async def update_publisher_route(
    publisher_id: int,
    data: PublisherUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):

    publisher = await update_publisher(
        session=session,
        publisher_id=publisher_id,
        data_in=data,
        payload=payload
    )

    return publisher


# Delete publisher
# Admin role required
@router.delete(
    "/{publisher_id}",
    response_model=PublisherDeleteResponse,
    summary="Delete publisher, set force=True, to delete all related data, Admin role required"
)
async def delete_publisher_route(
    publisher_id: int,

    force: bool = Query(
        default=False,
        description="Force delete publisher with linked books"
    ),

    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):

    result = await delete_publisher(
        session=session,
        publisher_id=publisher_id,
        force=force,
        payload=payload
    )

    return result
