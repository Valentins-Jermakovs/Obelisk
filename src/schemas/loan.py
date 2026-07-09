# =====================================================
#                       imports
# =====================================================
# Libraries:
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
# Models:
from models import LoanStatus



# ===================================================
#                       schemas
# ===================================================


# Loan create schema
class LoanCreate(BaseModel):
    
    book_copy_id: int
    reader_id: int
    library_id: int


# Loan update schema
class LoanUpdate(BaseModel):

    status: Optional[LoanStatus] = None
    return_date: Optional[datetime] = None
    fine_amount: Optional[float] = Field(default=None, ge=0)


# Loan book schema
class LoanBook(BaseModel):

    id: int
    title: str
    isbn: str
    inventory_code: str


# Loan reader schema
class LoanReader(BaseModel):

    id: int
    full_name: str
    email: str


# Loan library schema
class LoanLibrary(BaseModel):

    id: int
    name: str
    city: str


# Loan read schema
class LoanRead(BaseModel):

    id: int
    status: LoanStatus
    borrowed_at: datetime
    return_date: Optional[datetime]
    fine_amount: float
    reader: LoanReader
    library: LoanLibrary
    book: LoanBook

    class Config:
        from_attributes = True

# Library search read schema
class LoanSearchRead(BaseModel):

    id: int

    book_copy_id: int
    book_title: str
    reader_id: int
    reader_name: str
    library_id: int
    status: LoanStatus
    borrowed_at: datetime
    return_date: datetime | None
    fine_amount: float


# Loan search schema - wrapper for loan read schema
class LoanSearchResponse(BaseModel):

    items: list[LoanSearchRead]
    total: int
    limit: int
    offset: int
    returned: int


# Loan delete response schema
class LoanDeleteResponse(BaseModel):

    status: str
    loan_id: int

# Loan delete warning schema
class LoanDeleteWarning(BaseModel):

    warning: str
    message: str


# Reader loan read schema
class ReaderLoanRead(BaseModel):

    id: int
    book_title: str
    book_copy_id: int
    library_id: int
    library_name: str
    status: LoanStatus
    borrowed_at: datetime
    return_date: Optional[datetime]
    fine_amount: float


# Reader loan search schema
class ReaderLoanSearchResponse(BaseModel):

    items: list[ReaderLoanRead]

    total: int
    limit: int
    offset: int
    returned: int

# Loan delete response schema
class LoanDeleteResponse(BaseModel):

    status: str
    loan_id: int