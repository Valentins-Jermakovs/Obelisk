# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
# =====================================================


# Book <-> Genre association table
class BookGenre(SQLModel, table=True):

    # Table name
    __tablename__ = "book_genres"

    book_id: int | None = Field(default=None, foreign_key="dim_book.id", primary_key=True)
    genre_id: int | None = Field(default=None, foreign_key="dim_genre.id", primary_key=True)
