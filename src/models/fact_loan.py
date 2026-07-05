# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy import ForeignKey, Column
# =====================================================

class LoanStatus(str, Enum):
    ACTIVE = "active"
    LOST = "lost"
    RETURNED = "returned"
    OVERDUE = "overdue"


# Loan model
class FactLoan(SQLModel, table=True):

    # Table name
    __tablename__ = "fact_loans"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Foreign keys
    book_copy_id: int = Field(foreign_key="dim_book_copy.id", index=True)
    reader_id: int = Field(foreign_key="dim_reader.id", index=True)
    library_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_library.id", ondelete="CASCADE"),
            index=True
        )
    )

    # Fact attributes
    status: str = Field(default="active", index=True)


    borrowed_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        index=True
    )

    return_date: Optional[datetime] = Field(default=None)

    fine_amount: float = Field(default=0.0)