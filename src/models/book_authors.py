# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
# =====================================================


# Book <-> Author association table
class BookAuthor(SQLModel, table=True):

    # Table name
    __tablename__ = "book_authors"

    # Composite primary key
    book_id: int | None = Field(default=None, foreign_key="dim_book.id", primary_key=True)
    author_id: int | None = Field(default=None, foreign_key="dim_author.id", primary_key=True)
