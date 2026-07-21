# =====================================================
#                        Imports
# =====================================================

# Libraries:
from sqlmodel import SQLModel, Field



# =====================================================
#                       Models
# =====================================================

# Library model
class DimLibrary(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_library"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Library data
    name: str = Field(index=True, unique=True)
    city: str = Field(index=True)
    address: str