# ====================================================
#                       imports
# ====================================================
# Libraries:
from pydantic import BaseModel, Field
from datetime import date, datetime



# ===================================================
#                       schemas
# ===================================================

# Reader create
class ReaderCreate(BaseModel):

    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=5, max_length=255)
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9\s\-\(\)]{7,20}$")
    birth_date: date | None = None


# Reader update
class ReaderUpdate(BaseModel):

    full_name: str | None = None
    email: str | None = None
    phone: str | None = Field(default=None, pattern=r"^\+?[0-9\s\-\(\)]{7,20}$")
    birth_date: date | None = None


# Reader read
class ReaderRead(BaseModel):

    id: int
    full_name: str
    email: str
    phone: str | None = None
    birth_date: date | None = None
    registered_at: datetime | None = None

# Response
class ReaderSearchResponse(BaseModel):

    items: list[ReaderRead]

    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    returned: int = Field(ge=0)


# Reader delete response
class ReaderDeleteResponse(BaseModel):

    status: str