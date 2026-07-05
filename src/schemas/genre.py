# =====================================================
#                       imports
# =====================================================
from pydantic import BaseModel, Field
from typing import Optional, List
# =====================================================


# Create genre
class GenreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


# Update genre
class GenreUpdate(BaseModel):
    name: Optional[str] = None


# Read genre
class GenreRead(BaseModel):
    id: int
    name: str


# Optional: genre with books
class GenreWithBooks(BaseModel):
    id: int
    name: str
    books: List[dict] = []


# Search genre response
class GenreSearchResponse(BaseModel):
    items: List[GenreRead]

    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    returned: int = Field(ge=0)