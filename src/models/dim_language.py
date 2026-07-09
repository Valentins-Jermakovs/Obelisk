# =====================================================
#                       imports
# =====================================================
# Libraries:
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
# Models:
from .book_languages import BookLanguage



# =====================================================
#                       models
# =====================================================

# Type checking
if TYPE_CHECKING:
    from .dim_book import DimBook


# Language model
class DimLanguage(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_language"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Language code
    code: str = Field(
        index=True,
        unique=True,
        min_length=2,
        max_length=10
    )

    # Language name
    name: str | None = Field(
        default=None,
        index=True,
        max_length=100
    )

    # Foreign keys to BookLanguage table
    books: list["DimBook"] = Relationship(
        back_populates="languages",
        link_model=BookLanguage,
        sa_relationship_kwargs={"lazy": "selectin"}
    )
