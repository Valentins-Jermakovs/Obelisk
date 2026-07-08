# ===================================================
#                       imports
# ===================================================
#Libraries:
from fastapi import (
    APIRouter,
    Depends,
    Query
)
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Schemas:
from schemas.book_copy import (
    BookCopyCreate,
    BookCopyUpdate
)
# Services:
from services.book_copy.book_copy_service import (
    create_book_copy,
    update_book_copy,
    delete_book_copy,
    search_book_copies
)
# Utils:
from utils.token_utils import (
    validate_token, 
    librarian_required
)


# Router object for export
router = APIRouter(
    prefix="/book-copies",
    tags=["Book copies endpoints - [create, read, update, delete]"]
)



# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create physical book copy
# Return copy data
# Librarian role required
@router.post("/", summary="Create book copy, Librarian required")
async def create_copy(
    data: BookCopyCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)
):

    return await create_book_copy(
        session=session,
        data=data,
        payload=payload
    )



# Update book copy - update an existing physical copy by id
# Return updated copy data
# Librarian role required
@router.patch("/{copy_id}", summary="Update book copy, Librarian required")
async def update_copy(
    copy_id: int,
    data: BookCopyUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)
):

    return await update_book_copy(
        session=session,
        copy_id=copy_id,
        data=data,
        payload=payload
    )



# Delete book copy - delete an existing copy by id
# Return message or warning 
# Librarian role required
@router.delete("/{copy_id}", summary="Delete bookk copy, Librarian required")
async def delete_copy(
    copy_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)
):

    return await delete_book_copy(
        session=session,
        copy_id=copy_id,
        payload=payload
    )



# Search book copy
# Librarian role required
@router.get("/search", summary="Search book copy, Librarian required")
async def search_copy(
    query: str | None = Query(
        default=None,
        description="Search by book title, inventory code or shelf code"
    ),

    limit: int = Query(
        default=10,
        ge=1,
        le=100
    ),

    offset: int = Query(
        default=0,
        ge=0
    ),

    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)

):

    return await search_book_copies(
        session=session,
        payload=payload,
        query=query,
        limit=limit,
        offset=offset
    )