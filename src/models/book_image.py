# =====================================================
#                       imports
# =====================================================
from enum import Enum
from sqlmodel import SQLModel, Field
# =====================================================


# Image type enum
class BookImageType(str, Enum):
    COVER = "cover"
    BACK = "back"
    SPINE = "spine"
    PAGE = "page"
    DAMAGE = "damage"
    OTHER = "other"


# Book image model
class BookImage(SQLModel, table=True):

    # Table name
    __tablename__ = "book_images"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Book
    book_id: int = Field(foreign_key="dim_book.id", index=True)

    # Image path
    file_path: str

    # Image type
    image_type: BookImageType = Field(default=BookImageType.COVER)

    # Display order
    display_order: int = Field(default=0)