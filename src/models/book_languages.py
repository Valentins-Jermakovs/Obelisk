# =====================================================
#                       imports
# =====================================================
# Libraries:
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, ForeignKey



# =====================================================
#                       models
# =====================================================

# Book <-> Language association table
class BookLanguage(SQLModel, table=True):

    # Table name
    __tablename__ = "book_languages"

    # Composite primary key
    # Foreign key to Book table
    book_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_book.id", ondelete="CASCADE"),
            primary_key=True
        )
    )

    # Foreign key to Language table
    language_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_language.id", ondelete="CASCADE"),
            primary_key=True
        )
    )
