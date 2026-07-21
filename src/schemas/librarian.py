# =====================================================
#                        Imports
# =====================================================

# Libraries:
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional



# =====================================================
#                       Schemas
# =====================================================

# ===================Request schemas===================

# Librarian creation schema
class LibrarianCreate(BaseModel):
    
    # Username:
    full_name: str = Field(
        min_length=1, 
        max_length=255
    )

    # Email:
    email: EmailStr = Field(max_length=255)



# Librarian update schema
class LibrarianUpdate(BaseModel):

    # Full name
    full_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255
    )

    # Email
    email: Optional[EmailStr] = None



# ===================Response schemas================

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
    has_more: bool



# Link librarian to library response
class LibrarianLibraryLinkResponse(BaseModel):

    status: str | None = None
    message: str | None = None



# Remove librarian from library response
class LibrarianLibraryUnlinkResponse(BaseModel):

    status: str



# Delete librarian response
class LibrarianDeleteResponse(BaseModel):

    status: str
    removed_libraries_links: int