# =====================================================
#                       imports
# =====================================================
# Libraries:
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey



# =====================================================
#                       models
# =====================================================

# Book <-> Genre association table
class BookGenre(SQLModel, table=True):

    # Table name
    __tablename__ = "book_genres"

    book_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_book.id", ondelete="CASCADE"),
            primary_key=True
        )
    )

    genre_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_genre.id", ondelete="CASCADE"),
            primary_key=True
        )
    )
