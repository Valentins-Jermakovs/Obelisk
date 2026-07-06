# =====================================================
#                       imports
# =====================================================
# Libraries:
from sqlmodel import SQLModel, Field


# =====================================================
#                       models
# =====================================================

# Librarian model
class DimLibrarian(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_librarian"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Librarian data
    full_name: str = Field(index=True)
    email: str = Field(index=True, unique=True)