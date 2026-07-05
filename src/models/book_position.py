# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
# =====================================================


# Book physical position model
class BookPosition(SQLModel, table=True):

    # Table name
    __tablename__ = "book_position"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # id's of other tables
    book_copy_id: int = Field(foreign_key="dim_book_copy.id", index=True)
    shelf_id: int = Field(
        foreign_key="dim_shelf.id", 
        index=True,
        sa_column_kwargs={"ondelete": "CASCADE"}
    )

    # physical position data
    row: int | None = None
    column: int | None = None
    depth: int | None = None