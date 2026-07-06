# =====================================================
#                       imports
# =====================================================
# Libraries:
from sqlmodel import SQLModel, Field



# =====================================================
#                       models
# =====================================================

# Reader model
class DimReader(SQLModel, table=True):
    
    # Table name
    __tablename__ = "dim_reader"

    # Primary key
    id: int | None  = Field(
        default=None, 
        primary_key=True
    )
    
    # User data
    full_name: str = Field(index=True)
    email: str = Field(index=True, unique=True)