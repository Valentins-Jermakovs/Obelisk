# =====================================================
#                        Imports
# =====================================================

# Libraries:
from sqlmodel import SQLModel, Field



# =====================================================
#                       Models
# =====================================================

# Publisher model
class DimPublisher(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_publisher"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)


    # Publisher data:
    # Publisher name
    name: str = Field(
        index=True, 
        unique=True
    )
    # Country
    country: str | None = Field(
        default=None,
        index=True
    )