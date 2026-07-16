# ===================================================
#                       imports
# ===================================================
# Libraries:
from pydantic import BaseModel, Field
from typing import Optional




# ===================================================
#                       schemas
# ===================================================

# Author create schema
class AuthorCreate(BaseModel):

    # Author data:
    name: str = Field(min_length=1, max_length=255)
    country: Optional[str] = Field(default=None, max_length=100)
    birth_year: Optional[int] = Field(default=None, ge=0, le=2100)


# Author update schema
class AuthorUpdate(BaseModel):

    # Author data - mostly optional, for update only:
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    country: Optional[str] = Field(default=None, max_length=100)
    birth_year: Optional[int] = Field(default=None, ge=0, le=2100)


# Author read schema
class AuthorRead(BaseModel):

    id: int
    name: str
    country: Optional[str]
    birth_year: Optional[int]

    class Config:
        from_attributes = True


# Author delete response schema
class AuthorDeleteResponse(BaseModel):

    status: str


# Author delete warning schema
class AuthorDeleteWarning(BaseModel):

    warning: str
    books_count: int
    message: str

# Author search response schema
class AuthorSearchResponse(BaseModel):
    
    items: list["AuthorRead"]

    total: int
    limit: int
    offset: int
    returned: int