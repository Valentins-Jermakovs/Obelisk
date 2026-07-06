# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
from enum import Enum
from sqlalchemy import Column, ForeignKey
# =====================================================


class BookCondition(str, Enum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    DAMAGED = "damaged"
    LOST = "lost"

# Book copy model
class DimBookCopy(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_book_copy"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Book copy data
    book_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_book.id", ondelete="CASCADE"),
            index=True
        )
    )
    inventory_code: str = Field(index=True, unique=True)
    condition: BookCondition = Field(default=BookCondition.GOOD)