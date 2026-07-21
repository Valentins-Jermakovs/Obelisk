# =====================================================
#                        Imports
# =====================================================

# Libraries:
from pydantic import BaseModel, Field
from typing import Optional, List

# Models:
from models import BookImageType, BookCondition



# =====================================================
#                       Schemas
# =====================================================

# ===================Request schemas===================

# Images
class BookImageCreate(BaseModel):

    # Image path or address:
    file_path: str = Field(
        min_length=1, 
        max_length=500
    )

    # Image type:
    image_type: BookImageType = BookImageType.COVER

    # Display order, from 0 to n:
    display_order: int = 0



# Position of a physical copy
class BookPositionCreate(BaseModel):

    shelf_id: int
    row: Optional[int] = None
    column: Optional[int] = None
    depth: Optional[int] = None



# Book copy (physical copy)
class BookCopyCreate(BaseModel):

    inventory_code: str = Field(
        min_length=1, 
        max_length=50
    )

    condition: BookCondition = BookCondition.GOOD

    position: BookPositionCreate



# MAIN CREATE SCHEMA
class BookCreate(BaseModel):

    # Basic book data:
    title: str = Field(min_length=1, max_length=255)
    isbn: str = Field(min_length=5, max_length=20)
    publication_year: int = Field(ge=0, le=2100)

    # Optional data:
    annotation: Optional[str] = Field(default=None)
    publisher_id: Optional[int] = None
    pages: Optional[int] = Field(default=None, ge=1)

    # Relations (allow empty lists safely)
    authors: List[int] = Field(default_factory=list)
    genres: List[int] = Field(default_factory=list)
    languages: List[int] = Field(default_factory=list)

    # Optional media
    images: List[BookImageCreate] = Field(default_factory=list)

    # Physical copies
    copies: List[BookCopyCreate] = Field(default_factory=list)



# UPDATE SCHEMA
class BookUpdate(BaseModel):

    # Basic book data (optional):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(default=None, min_length=5, max_length=20)
    annotation: Optional[str] = None
    publication_year: Optional[int] = Field(default=None, ge=0, le=2100)
    publisher_id: Optional[int] = None
    pages: Optional[int] = Field(default=None, ge=1)

    # Relations
    authors: Optional[List[int]] = None
    genres: Optional[List[int]] = None
    languages: Optional[List[int]] = None

    # Optional media
    images: Optional[List[BookImageCreate]] = None
    copies: Optional[List[BookCopyCreate]] = None



# ===================Response schemas================

# Publisher short schema
class PublisherShort(BaseModel):

    id: int
    name: str



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
    publisher_id: Optional[int] = None
    pages: Optional[int] = None
    publisher: Optional[PublisherShort] = None

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
    publisher_id: Optional[int] = None
    pages: Optional[int] = None
    publisher: Optional[PublisherShort] = None

    availability: BookAvailability
    libraries: List[LibraryAvailability] = []



# Book search response schema
class BookSearchResponse(BaseModel):

    items: list[BookSearchItem]

    total: int
    limit: int
    offset: int
    has_more: bool



# Book delete response schema
class BookDeleteResponse(BaseModel):

    status: str



# Book delete warning schema
class BookDeleteWarning(BaseModel):
    
    warning: str
    copies_count: int | None = None
    message: str
    blocked_reason: Optional[str] = None