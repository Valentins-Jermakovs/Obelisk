# ====================================================
#                       imports
# ====================================================
from pydantic import BaseModel, Field
from typing import List, Optional
# ===================================================


# Librarian creation schema
class LibrarianCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=5, max_length=255)

# Librarian update schema
class LibrarianUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None

# Library short schema
class LibraryShort(BaseModel):
    id: int
    name: str
    city: str

# Librarian read schema
class LibrarianRead(BaseModel):
    id: int
    full_name: str
    email: str


# Librarian read with libraries schema
class LibrarianWithLibraries(BaseModel):
    id: int
    full_name: str
    email: str
    libraries: List[LibraryShort]

# Librarian search response schema
class LibrarianSearchResponse(BaseModel):
    items: List[LibrarianWithLibraries]

    total: int
    limit: int
    offset: int
    returned: int