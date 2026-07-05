# =====================================================
#                       imports
# =====================================================
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .book_genres import BookGenre
# =====================================================

if TYPE_CHECKING:
    from .dim_book import DimBook


# Genre model
class DimGenre(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_genre"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)

    books: list["DimBook"] = Relationship(back_populates="genres", link_model=BookGenre)
