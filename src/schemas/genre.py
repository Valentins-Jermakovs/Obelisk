# =====================================================
#                        Imports
# =====================================================

# Libraries:
from pydantic import BaseModel, Field
from typing import Optional, List



# =====================================================
#                       Schemas
# =====================================================

# ===================Request schemas===================

# Create genre
class GenreCreate(BaseModel):

    name: str = Field(
        min_length=1, 
        max_length=100
    )



# Update genre
class GenreUpdate(BaseModel):

    name: Optional[str] = None



# ===================Response schemas================

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

    total: int
    limit: int
    offset: int
    has_more: bool


# Genre delete response
class GenreDeleteResponse(BaseModel):

    status: str