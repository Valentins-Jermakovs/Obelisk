# =====================================================
#                        Imports
# =====================================================

# Libraries:
from sqlmodel import SQLModel, Field
from datetime import datetime, date


# =====================================================
#                       Models
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
    

    # User data:
    # Username
    full_name: str = Field(
        index=True, 
        max_length=255
    )

    # Email
    email: str = Field(
        unique=True,
        index=True,
        max_length=255
    )

    # Phone
    phone: str | None = Field(
        default=None,
        max_length=20
    )

    # Birth date
    birth_date: date | None = Field(
        default=None
    )

    # Registration
    registered_at: datetime = Field(
        default_factory=datetime.now
    )