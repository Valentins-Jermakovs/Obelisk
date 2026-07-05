# =====================================================
#                       imports
# =====================================================
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .book_authors import BookAuthor
from .book_genres import BookGenre
from .book_languages import BookLanguage
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
    annotation: str | None = Field(default=None)
    publication_year: int

    authors: list["DimAuthor"] = Relationship(back_populates="books", link_model=BookAuthor)
    genres: list["DimGenre"] = Relationship(back_populates="books", link_model=BookGenre)
    languages: list["DimLanguage"] = Relationship(back_populates="books", link_model=BookLanguage)