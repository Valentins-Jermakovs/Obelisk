# =====================================================
#                       imports
# =====================================================
# Libraries:
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey


# =====================================================
#                       models
# =====================================================

# Book <-> Author association table
class BookAuthor(SQLModel, table=True):

    # Table name
    __tablename__ = "book_authors"

    # Composite primary key
    book_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_book.id", ondelete="CASCADE"),
            primary_key=True
        )
    )

    author_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_author.id", ondelete="CASCADE"),
            primary_key=True
        )
    )
