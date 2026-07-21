# =====================================================
#                        Imports
# =====================================================

# Libraies:
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import ForeignKey, Column



# =====================================================
#                       Models
# =====================================================

# ======================Enums==========================

# Enum for loan status
class LoanStatus(str, Enum):
    
    ACTIVE = "active"
    LOST = "lost"
    RETURNED = "returned"
    OVERDUE = "overdue"



# ======================Models=========================

# Loan model
class FactLoan(SQLModel, table=True):

    # Table name
    __tablename__ = "fact_loans"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)


    # Foreign keys
    # Foreign key to DimBookCopy table
    book_copy_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_book_copy.id", ondelete="CASCADE"),
            index=True
        )
    )

    # Foreign key to DimReader table
    reader_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_reader.id", ondelete="CASCADE"),
            index=True
        )
    )

    # Foreign key to DimLibrary table
    library_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_library.id", ondelete="CASCADE"),
            index=True
        )
    )


    # Other attributes
    # Loan status
    status: str = Field(default="active", index=True)

    # Borrowed at
    borrowed_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        index=True
    )

    # Returned at (optional)
    return_date: Optional[datetime] = Field(default=None)

    # Fine amount (default 0.0)
    fine_amount: float = Field(default=0.0)