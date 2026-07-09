# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Services:
from services.language_service import (
    create_language,
    search_languages,
    update_language,
    delete_language
)
# Schemas
from schemas.language import (
    LanguageCreate, 
    LanguageUpdate, 
    LanguageRead, 
    LanguageSearchResponse,
    LanguageDeleteResponse
)
# Utils:
from utils.token_utils import admin_required, admin_or_librarian_required



# Router object for export
router = APIRouter(
    prefix="/languages", 
    tags=["Languages endpoints - [create, read, update, delete]"]
)

# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create language
# Return language object
# Administrator role required
@router.post(
    "/", 
    response_model=LanguageRead,
    summary="Create language, Admin required"
)
async def create(
    data: LanguageCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await create_language(
        session=session, 
        data_in=data
    )


# Search languages - search by name
# Administrator or Librarian role required
@router.get(
    "/search", 
    response_model=LanguageSearchResponse,
    summary="Create language, Admin or Librarian required"
)
async def search(
    query: str | None = Query(default=None),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_or_librarian_required)
):
    return await search_languages(
        session=session,
        query=query,
        limit=limit,
        offset=offset
    )


# Update language - by id
# Administrator role required
@router.patch(
    "/{language_id}", 
    response_model=LanguageRead,
    summary="Update language, Admin required"
)
async def update(
    language_id: int,
    data: LanguageUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await update_language(
        session=session, 
        language_id=language_id, 
        data_in=data
    )


# Delete language - by id
# Administrator role required
@router.delete(
    "/{language_id}",
    response_model=LanguageDeleteResponse,
    summary="Delete language, set force=True to delete entities, Admin required"
)
async def delete(
    language_id: int,
    force: bool = Query(False),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_language(
        session=session, 
        language_id=language_id, 
        force=force
    )