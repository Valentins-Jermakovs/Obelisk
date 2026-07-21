# =====================================================
#                        Imports
# =====================================================

# Libraries:
from pydantic import BaseModel, Field

# Models:
from models import BookCondition



# =====================================================
#                       Schemas
# =====================================================

# ===================Request schemas===================

# Book copy create schema
class BookCopyCreate(BaseModel):

    # FK data:
    book_id: int
    library_id: int
    shelf_id: int

    # Inventory code:
    inventory_code: str = Field(
        min_length=1,
        max_length=50
    )

    # Book condition and position:
    condition: BookCondition = BookCondition.GOOD
    row: int | None = None
    column: int | None = None
    depth: int | None = None



# Book copy update schema
class BookCopyUpdate(BaseModel):

    # Inventory code:
    inventory_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    # Book condition and position:
    condition: BookCondition | None = None
    shelf_id: int | None = None
    row: int | None = None
    column: int | None = None
    depth: int | None = None



# ===================Response schemas================

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
    has_more: bool