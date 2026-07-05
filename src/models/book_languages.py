# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
# =====================================================


# Book <-> Language association table
class BookLanguage(SQLModel, table=True):

    # Table name
    __tablename__ = "book_languages"

    book_id: int | None = Field(default=None, foreign_key="dim_book.id", primary_key=True)
    language_id: int | None = Field(default=None, foreign_key="dim_language.id", primary_key=True)
