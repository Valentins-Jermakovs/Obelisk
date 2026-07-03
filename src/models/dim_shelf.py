# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
# =====================================================


# Shelf model
class DimShelf(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_shelf"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Library id
    library_id: int = Field(foreign_key="dim_library.id", index=True)

    # Shelf data
    code: str = Field(index=True)   # A-01, B-12
    section: str | None = None