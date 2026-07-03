# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
# =====================================================

# Loan model
class FactLoan(SQLModel, table=True):

    # Table name
    __tablename__ = "fact_loans"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Foreign keys
    book_id: int = Field(foreign_key="dim_book.id", index=True)
    reader_id: int = Field(foreign_key="dim_reader.id", index=True)
    date_id: int = Field(foreign_key="dim_date.id", index=True)
    library_id: int = Field(foreign_key="dim_library.id", index=True)

    # Fact attributes
    status: str = Field(default="active", index=True)


    borrowed_at: datetime = Field(
        default_factory=lambda: datetime.now(),
        index=True
    )

    return_date: Optional[datetime] = Field(default=None)

    fine_amount: float = Field(default=0.0)