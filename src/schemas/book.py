# ===================================================
#                       imports
# ===================================================
from pydantic import BaseModel, Field
from typing import Optional, List
from models import BookImageType, BookCondition
# ===================================================


# ===================================================
#               schemas - Create book
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



class AuthorShort(BaseModel):
    id: int
    name: str


class GenreShort(BaseModel):
    id: int
    name: str


class LanguageShort(BaseModel):
    id: int
    code: str
    name: Optional[str] = None


class ImageRead(BaseModel):
    id: int
    file_path: str
    image_type: str
    display_order: int


class CopyRead(BaseModel):
    id: int
    inventory_code: str
    condition: str


class BookAvailability(BaseModel):
    status: str
    total_copies: int
    available_copies: int
    active_loans: int


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