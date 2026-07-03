# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
from datetime import date
# =====================================================


# Date model
class DimDate(SQLModel, table=True):

    # Table name
    __tablename__ = "dim_date"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Full date
    full_date: date = Field(index=True, unique=True)

    # Dates
    day: int
    month: int
    year: int