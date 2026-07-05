# =====================================================
#                       imports
# =====================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# DB:
from config.db_dependency import get_db
# Services:
from services.language_service import (
    create_language,
    search_languages,
    update_language,
    delete_language
)
# Schemas
from schemas.language import LanguageCreate, LanguageUpdate, LanguageRead, LanguageSearchResponse
# Utils:
from utils.token_utils import admin_required
# =====================================================


# =====================================================
#                       Router
# =====================================================
router = APIRouter(
    prefix="/languages", 
    tags=["Languages"]
)

# =====================================================
#                       Endpoints
# =====================================================

# Create language
@router.post("", response_model=LanguageRead)
async def create(
    data: LanguageCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await create_language(session, data)


# Search languages
@router.get("/search", response_model=LanguageSearchResponse)
async def search(
    query: str | None = Query(default=None),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await search_languages(
        session=session,
        query=query,
        limit=limit,
        offset=offset
    )


# Update language
@router.patch("/{language_id}", response_model=LanguageRead)
async def update(
    language_id: int,
    data: LanguageUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await update_language(session, language_id, data)


# Delete language
@router.delete("/{language_id}")
async def delete(
    language_id: int,
    force: bool = Query(False),
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(admin_required)
):
    return await delete_language(session, language_id, force)