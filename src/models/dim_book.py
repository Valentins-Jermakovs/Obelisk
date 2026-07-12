# =====================================================
#                       imports
# =====================================================
# Libraries:
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import ForeignKey, Column
# Models:
from .book_authors import BookAuthor
from .book_genres import BookGenre
from .book_languages import BookLanguage



# =====================================================
#                       models
# =====================================================

# Type checking
if TYPE_CHECKING:
    from .dim_author import DimAuthor
    from .dim_genre import DimGenre
    from .dim_language import DimLanguage


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
    pages: int | None = Field(default=None, ge=1)


    # Relationships
    # Foreign key to DimAuthor table
    authors: list["DimAuthor"] = Relationship(
        back_populates="books", 
        link_model=BookAuthor
    )

    # Foreign key to DimGenre table
    genres: list["DimGenre"] = Relationship(
        back_populates="books", 
        link_model=BookGenre
    )

    # Foreign key to DimLanguage table
    languages: list["DimLanguage"] = Relationship(
        back_populates="books", 
        link_model=BookLanguage
    )

    # Foreign key to DimPublisher table
    publisher_id: int | None = Field(
        sa_column=Column(
            ForeignKey("dim_publisher.id", ondelete="SET NULL"),
        )
    )