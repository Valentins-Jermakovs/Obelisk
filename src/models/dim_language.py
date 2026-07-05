# =====================================================
#                       imports
# =====================================================
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .book_languages import BookLanguage
# =====================================================

if TYPE_CHECKING:
    from .dim_book import DimBook


# Language model
class DimLanguage(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_language"

    id: int | None = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True)
    name: str | None = Field(default=None)

    books: list["DimBook"] = Relationship(back_populates="languages", link_model=BookLanguage)
