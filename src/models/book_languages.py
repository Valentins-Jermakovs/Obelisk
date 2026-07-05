# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey
# =====================================================


# Book <-> Language association table
class BookLanguage(SQLModel, table=True):

    # Table name
    __tablename__ = "book_languages"

    book_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_book.id", ondelete="CASCADE"),
            primary_key=True
        )
    )

    language_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_language.id", ondelete="CASCADE"),
            primary_key=True
        )
    )
