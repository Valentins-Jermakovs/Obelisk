# =====================================================
#                        Imports
# =====================================================

# Libraries:
from sqlmodel import SQLModel, Field
from sqlalchemy import ForeignKey, Column



# =====================================================
#                       Models
# =====================================================

# Book physical position model
class BookPosition(SQLModel, table=True):

    # Table name
    __tablename__ = "book_position"

    # Primary key
    id: int | None = Field(default=None, primary_key=True)


    # ID's of other tables
    # Foreign key to BookCopy table
    book_copy_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_book_copy.id", ondelete="CASCADE"),
            index=True
        )
    )

    # Foreign key to Shelf table
    shelf_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_shelf.id", ondelete="CASCADE"),
            index=True
        )
    )


    # Physical position data
    row: int | None = None
    column: int | None = None
    depth: int | None = None