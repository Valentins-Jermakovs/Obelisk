# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
# =====================================================

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

    author_id: int = Field(foreign_key="dim_author.id")