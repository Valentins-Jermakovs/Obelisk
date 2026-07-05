# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
from sqlalchemy import ForeignKey, Column
# =====================================================

# dim_librarian <-> librarian_library <-> dim_library (M2M)
class LibrarianLibrary(SQLModel, table=True):

    # Table name
    __tablename__ = "librarian_library"

    # Relationships
    librarian_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_librarian.id", ondelete="CASCADE"),
            primary_key=True
        )
    )

    library_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_library.id", ondelete="CASCADE"),
            primary_key=True
        )
    )