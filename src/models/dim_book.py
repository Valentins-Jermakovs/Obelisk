# =====================================================
#                       imports
# =====================================================
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .book_authors import BookAuthor
# =====================================================

if TYPE_CHECKING:
    from .dim_author import DimAuthor


# Book model
class DimBook(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_book"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Book data
    title: str = Field(index=True)
    isbn: str = Field(index=True, unique=True)
    genre: str = Field(index=True)
    language: str = Field(default="en")
    publication_year: int

    authors: list["DimAuthor"] = Relationship(back_populates="books", link_model=BookAuthor)