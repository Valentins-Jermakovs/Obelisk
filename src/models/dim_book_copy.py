# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
# =====================================================


# Book copy model
class DimBookCopy(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_book_copy"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Book copy data
    book_id: int = Field(foreign_key="dim_book.id", index=True)
    inventory_code: str = Field(index=True, unique=True)
    condition: str = Field(default="good", index=True)