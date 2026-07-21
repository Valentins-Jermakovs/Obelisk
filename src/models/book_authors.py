# =====================================================
#                        Imports
# =====================================================

# Libraries:
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey


# =====================================================
#                       Models
# =====================================================

# Book <-> Author association table
class BookAuthor(SQLModel, table=True):

    # Table name
    __tablename__ = "book_authors"

    # Composite primary key
    # Foreign key to dim_book table
    book_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_book.id", ondelete="CASCADE"),
            primary_key=True
        )
    )

    # Foreign key to dim_author table
    author_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_author.id", ondelete="CASCADE"),
            primary_key=True
        )
    )
