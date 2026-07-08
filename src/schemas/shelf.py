# =====================================================
#                       imports
# =====================================================
from pydantic import BaseModel, Field
from typing import Optional



# ===================================================
#                       schemas
# ===================================================

# Create shelf schema
class ShelfCreate(BaseModel):

    library_id: int
    code: str = Field(min_length=1, max_length=20)
    section: Optional[str] = Field(default=None, max_length=100)


# Update shelf schema
class ShelfUpdate(BaseModel):

    code: Optional[str] = Field(default=None, min_length=1, max_length=20)
    section: Optional[str] = Field(default=None, max_length=100)


# Read shelf schema
class ShelfRead(BaseModel):

    id: int
    library_id: int
    code: str
    section: Optional[str] = None


# Search shelf schema - wrapper
class ShelfSearchResponse(BaseModel):

    items: list[ShelfRead]

    total: int
    returned: int

    library_total_shelves: int
    library_remaining: int


# Delete shelf response schema
class ShelfDeleteResponse(BaseModel):

    status: str