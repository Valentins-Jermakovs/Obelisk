# ===================================================
#                       imports
# ===================================================
# Libraries:
from pydantic import BaseModel, Field
from models import BookCondition

# ===================================================
#                       schemas
# ===================================================

# Book copy create schema
class BookCopyCreate(BaseModel):

    book_id: int
    library_id: int
    shelf_id: int

    inventory_code: str = Field(
        min_length=1,
        max_length=50
    )

    condition: BookCondition = BookCondition.GOOD
    row: int | None = None
    column: int | None = None
    depth: int | None = None


# Book copy update schema
class BookCopyUpdate(BaseModel):

    inventory_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    condition: BookCondition | None = None
    shelf_id: int | None = None
    row: int | None = None
    column: int | None = None
    depth: int | None = None


# Response after create/update
class BookCopyRead(BaseModel):

    id: int
    book_id: int
    inventory_code: str
    condition: BookCondition



# Delete response
class BookCopyDeleteResponse(BaseModel):

    status: str
    copy_id: int



# Shelf information in search response
class BookCopyShelfRead(BaseModel):

    code: str
    row: int | None = None
    column: int | None = None
    depth: int | None = None



# Single search item
class BookCopySearchItem(BaseModel):

    id: int
    book_id: int
    title: str
    inventory_code: str
    condition: BookCondition
    library_id: int
    shelf: BookCopyShelfRead
    loan_status: str



# Search pagination response
class BookCopySearchResponse(BaseModel):

    items: list[BookCopySearchItem]

    total: int
    limit: int
    offset: int
    returned: int