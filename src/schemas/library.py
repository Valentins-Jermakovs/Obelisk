# ===================================================
#                       imports
# ===================================================
# Libraries:
from pydantic import BaseModel, Field
from typing import Optional



# ===================================================
#                       schemas
# ===================================================

# Library create schema
class LibraryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=1, max_length=255)


# Library update schema
class LibraryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    city: Optional[str] = Field(default=None, min_length=1, max_length=100)
    address: Optional[str] = Field(default=None, min_length=1, max_length=255)


# Library read schema
class LibraryRead(BaseModel):
    id: int
    name: str
    city: str
    address: str


# Library delete response schema
class LibraryDeleteResponse(BaseModel):
    status: str
    forced: bool = False


# Library delete warning respons
class LibraryDeleteWarning(BaseModel):
    warning: str
    details: dict
    message: str

# Search response schema
class LibrarySearchResponse(BaseModel):
    items: list["LibraryRead"]

    total: int
    limit: int
    offset: int
    returned: int