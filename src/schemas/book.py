# ===================================================
#                       imports
# ===================================================
# Libraries:
from pydantic import BaseModel, Field
from typing import Optional, List
# Models:
from models import BookImageType, BookCondition



# ===================================================
#                      schemas
# ===================================================

# Images
class BookImageCreate(BaseModel):

    file_path: str = Field(min_length=1, max_length=500)
    image_type: BookImageType = BookImageType.COVER
    display_order: int = 0


# Position of a physical copy
class BookPositionCreate(BaseModel):

    shelf_id: int
    row: Optional[int] = None
    column: Optional[int] = None
    depth: Optional[int] = None


# Book copy (physical copy)
class BookCopyCreate(BaseModel):

    inventory_code: str = Field(min_length=1, max_length=50)
    condition: BookCondition = BookCondition.GOOD

    position: BookPositionCreate



# MAIN CREATE SCHEMA
class BookCreate(BaseModel):

    title: str = Field(min_length=1, max_length=255)
    isbn: str = Field(min_length=5, max_length=20)

    annotation: Optional[str] = Field(default=None)
    publication_year: int = Field(ge=0, le=2100)

    # relations (allow empty lists safely)
    authors: List[int] = Field(default_factory=list)
    genres: List[int] = Field(default_factory=list)
    languages: List[int] = Field(default_factory=list)

    # optional media
    images: List[BookImageCreate] = Field(default_factory=list)

    # physical copies (can be empty if digital-only in future)
    copies: List[BookCopyCreate] = Field(default_factory=list)


# UPDATE SCHEMA
class BookUpdate(BaseModel):

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, min_length=5, max_length=20)

    annotation: Optional[str] = None
    publication_year: Optional[int] = Field(default=None, ge=0, le=2100)

    # relations
    authors: Optional[List[int]] = None
    genres: Optional[List[int]] = None
    languages: Optional[List[int]] = None

    # full replace strategy (проще и безопаснее)
    images: Optional[List[BookImageCreate]] = None
    copies: Optional[List[BookCopyCreate]] = None


# Author short schema
class AuthorShort(BaseModel):

    id: int
    name: str


# Genre short schema
class GenreShort(BaseModel):

    id: int
    name: str


# Language short schema
class LanguageShort(BaseModel):

    id: int
    code: str
    name: Optional[str] = None


# Image short schema
class ImageRead(BaseModel):

    id: int
    file_path: str
    image_type: str
    display_order: int


# Book position schema
class BookPositionRead(BaseModel):

    row: Optional[int] = None
    column: Optional[int] = None
    depth: Optional[int] = None


# Shelf short schema
class ShelfShort(BaseModel):

    id: int
    code: str
    section: Optional[str] = None


# Book copy read schema
class CopyRead(BaseModel):

    id: int
    inventory_code: str
    condition: str
    shelf: Optional[ShelfShort] = None
    position: Optional[BookPositionRead] = None


# Book availability schema
class BookAvailability(BaseModel):

    status: str
    total_copies: int
    available_copies: int
    active_loans: int


# Book read schema
class BookRead(BaseModel):

    id: int
    title: str
    isbn: str
    annotation: Optional[str]
    publication_year: int

    authors: List[AuthorShort]
    genres: List[GenreShort]
    languages: List[LanguageShort]

    images: List[ImageRead]
    copies: List[CopyRead]

    availability: BookAvailability

    # libraries where copies are located with availability per library
    libraries: List["LibraryAvailability"] = []


# Library short schema
class LibraryShort(BaseModel):

    id: int
    name: str
    city: str
    address: str


# Library availability schema
class LibraryAvailability(BaseModel):

    id: int
    name: str
    city: str
    address: str

    total_copies: int
    available_copies: int
    active_loans: int


# Book search schema
class BookSearchItem(BaseModel):

    id: int
    title: str
    isbn: str
    annotation: Optional[str]
    publication_year: int

    availability: BookAvailability
    libraries: List[LibraryAvailability] = []


# Book search response schema
class BookSearchResponse(BaseModel):

    items: list[BookSearchItem]

    total: int
    limit: int
    offset: int
    returned: int


# Book delete response schema
class BookDeleteResponse(BaseModel):

    status: str


# Book delete warning schema
class BookDeleteWarning(BaseModel):
    
    warning: str
    copies_count: int | None = None
    message: str
    blocked_reason: Optional[str] = None