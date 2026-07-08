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