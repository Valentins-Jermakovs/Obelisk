# ====================================================
#                       imports
# ====================================================
# Libraries:
from pydantic import BaseModel, Field



# ===================================================
#                       schemas
# ===================================================

# Reader create
class ReaderCreate(BaseModel):

    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=5, max_length=255)


# Reader update
class ReaderUpdate(BaseModel):

    full_name: str | None = None
    email: str | None = None


# Reader read
class ReaderRead(BaseModel):

    id: int
    full_name: str
    email: str

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