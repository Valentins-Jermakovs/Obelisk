# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
# Dependencies:
from config.db_dependency import get_db
# Services
from services.loan.loan_service import (
    create_loan,
    update_loan,
    delete_loan,
    search_loans,
    get_reader_loans
)
# Schemas
from schemas.loan import (
    LoanCreate,
    LoanUpdate,
    LoanRead,
    LoanSearchResponse,
    ReaderLoanSearchResponse
)
# Utils:
from utils.token_utils import librarian_required, validate_token


# Router object for export
router = APIRouter(
    prefix="/loans",
    tags=["Loans endpoints - [create, read, update, delete]"]
)


# ==================================================
#       routes - create, read, update, delete
# ==================================================

# Create a loan
# Librarian role required
@router.post(
    "/",
    response_model=LoanRead,
    summary="Create a loan, Librarian required",
)
async def create(
    data: LoanCreate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)
):

    return await create_loan(
        session=session,
        data=data,
        payload=payload
    )


# Update loan by ID
# Librarian role required
@router.patch(
    "/{loan_id}",
    response_model=LoanRead,
    summary="Update a loan by ID, Librarian required",
)
async def update(
    loan_id: int,
    data: LoanUpdate,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)
):

    return await update_loan(
        session=session,
        loan_id=loan_id,
        data=data,
        payload=payload
    )


# Delete loan by ID
# Librarian role required
@router.delete(
    "/{loan_id}",
    summary="Delete a loan by ID, Librarian required",
)
async def delete(
    loan_id: int,
    session: AsyncSession = Depends(get_db),
    payload: dict = Depends(librarian_required)
):

    return await delete_loan(
        session=session,
        loan_id=loan_id,
        payload=payload
    )


# Search loan by reader name or book title
# Librarian role required
@router.get(
    "/search",
    response_model=LoanSearchResponse,
    summary="Search a loan for librarian, Librarian required",
)
async def search(
    query: str | None = Query(
        default=None,
        min_length=1
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

    return await search_loans(
        session=session,
        query=query,
        payload=payload,
        limit=limit,
        offset=offset
    )


# Search loans for reader
# Reader required
@router.get(
    "/my",
    response_model=ReaderLoanSearchResponse,
    summary="Search a loan for reader, reader ID required",
)
async def my_loans(
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
    payload: dict = Depends(validate_token)
):

    return await get_reader_loans(
        session=session,
        payload=payload,
        limit=limit,
        offset=offset
    )