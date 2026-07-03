# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
from typing import Optional
# =====================================================

# Author model
class DimAuthor(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_author"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Author data
    name: str = Field(index=True)
    country: Optional[str] = Field(default=None, index=True)
    birth_year: Optional[int] = Field(default=None)