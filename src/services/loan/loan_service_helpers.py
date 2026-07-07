# ===================================================
#                       imports
# ===================================================
# Libraries:
from fastapi import HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
# Models:
from models import (
    DimReader,
    DimBookCopy,
    DimShelf,
    BookPosition,
    FactLoan,
    LoanStatus,
    DimLibrarian,
    LibrarianLibrary
)



# ===================================================
#                  Helper functions
# ===================================================

# Get librarian email from access token payload
async def _get_librarian_from_payload(
    session: AsyncSession,
    payload: dict
) -> DimLibrarian | None:
    
    # If token is invalid or does not contain librarian role
    if "librarian" not in payload.get("roles", []):
        return None

    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token payload"
        )

    # Try to get librarian from database
    librarian = (await session.exec(
        select(DimLibrarian).where(DimLibrarian.email == email)
    )).first()

    # Raise error if librarian not found
    if not librarian:
        raise HTTPException(
            status_code=404,
            detail="Librarian not found"
        )

    return librarian


# Check librarian access to library
async def _validate_librarian_access_to_library(
    session: AsyncSession,
    payload: dict,
    library_id: int
):
    # Admin can access any library
    if "admin" in payload.get("roles", []):
        return

    # Get librarian
    librarian = await _get_librarian_from_payload(
        session,
        payload
    )

    # Check assignment
    assignment = (
        await session.exec(
            select(LibrarianLibrary).where(
                LibrarianLibrary.librarian_id == librarian.id,
                LibrarianLibrary.library_id == library_id
            )
        )
    ).first()

    if not assignment:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this library"
        )


# Check reader exists
async def _validate_reader(
    session: AsyncSession,
    reader_id: int
) -> DimReader:

    # Get reader
    reader = await session.get(DimReader, reader_id)

    if not reader:
        raise HTTPException(
            status_code=404,
            detail="Reader not found"
        )

    return reader


# Check book copy exists
async def _validate_book_copy(
    session: AsyncSession,
    copy_id: int
) -> DimBookCopy:

    # Get book copy
    copy = await session.get(DimBookCopy, copy_id)

    if not copy:
        raise HTTPException(
            status_code=404,
            detail="Book copy not found"
        )

    return copy


# Check that copy belongs to selected library
async def _validate_copy_library(
    session: AsyncSession,
    copy_id: int,
    library_id: int
):

    # Get book copy
    position = (
        await session.exec(
            select(BookPosition).where(
                BookPosition.book_copy_id == copy_id
            )
        )
    ).first()


    # Check position exists
    if not position:
        raise HTTPException(
            status_code=404,
            detail="Book position not found"
        )

    # Get shelf
    shelf = await session.get(
        DimShelf,
        position.shelf_id
    )

    # Check shelf exists
    if not shelf:
        raise HTTPException(
            status_code=404,
            detail="Shelf not found"
        )

    # Check library id matches with shelf's one
    if shelf.library_id != library_id:
        raise HTTPException(
            status_code=409,
            detail="Book copy belongs to another library"
        )
    

# Check that copy is available
async def _check_copy_available(
    session: AsyncSession,
    copy_id: int
):

    # Get loan
    loan = (
        await session.exec(
            select(FactLoan).where(
                FactLoan.book_copy_id == copy_id,
                FactLoan.status.in_([
                    LoanStatus.ACTIVE,
                    LoanStatus.OVERDUE,
                    LoanStatus.LOST
                ])
            )
        )
    ).first()

    # Check if there is a loan for this copy
    if loan:
        raise HTTPException(
            status_code=409,
            detail="Book copy is already borrowed"
        )

# Get loan by ID
async def _get_loan(
    session: AsyncSession,
    loan_id: int
) -> FactLoan:

    loan = await session.get(FactLoan, loan_id)

    if not loan:
        raise HTTPException(
            status_code=404,
            detail="Loan not found"
        )

    return loan

# Create loan object
async def _create_loan(
    session: AsyncSession,
    data
) -> FactLoan:

    # Create loan object
    loan = FactLoan(
        book_copy_id=data.book_copy_id,
        reader_id=data.reader_id,
        library_id=data.library_id,
        status=LoanStatus.ACTIVE,
        fine_amount=0
    )

    session.add(loan)

    await session.flush()

    return loan

# Get loan by ID
async def _get_accessible_loan(
    session: AsyncSession,
    payload: dict,
    loan_id: int
) -> FactLoan:
    
    # Get loan object
    loan = await _get_loan(session, loan_id)

    await _validate_librarian_access_to_library(
        session,
        payload,
        loan.library_id
    )

    return loan


# Get accessible library IDs
async def _get_accessible_library_ids(
    session: AsyncSession,
    payload: dict
):

    # Get librarian ID
    librarian = await _get_librarian_from_payload(
        session,
        payload
    )

    # Get accessible library IDs
    rows = await session.exec(
        select(LibrarianLibrary.library_id)
        .where(
            LibrarianLibrary.librarian_id == librarian.id
        )
    )


    return rows.all()


# Get reader email from payload
async def _get_reader_from_payload(
    session: AsyncSession,
    payload: dict
):

    # Get email from payload
    email = payload.get("email")


    if not email:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    # Get reader from database
    reader = (
        await session.exec(
            select(DimReader)
            .where(
                DimReader.email == email
            )
        )
    ).first()


    if not reader:
        raise HTTPException(
            status_code=404,
            detail="Reader not found"
        )


    return reader