# =====================================================
#                       imports
# =====================================================
# Libraries:
from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship
# Models:
from .book_authors import BookAuthor



# =====================================================
#                       models
# =====================================================

# Type checking
if TYPE_CHECKING:
    from .dim_book import DimBook


# Author model
class DimAuthor(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_author"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Author data
    name: str = Field(index=True, unique=True)
    country: Optional[str] = Field(default=None, index=True)
    birth_year: Optional[int] = Field(default=None)

    # Foreign key to book authors association table
    books: list["DimBook"] = Relationship(
        back_populates="authors", 
        link_model=BookAuthor
    )