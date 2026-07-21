# =====================================================
#                        Imports
# =====================================================

# Libraries:
from sqlmodel import SQLModel, Field
from sqlalchemy import ForeignKey, Column



# =====================================================
#                       Models
# =====================================================

# dim_librarian <-> librarian_library <-> dim_library (M2M)
class LibrarianLibrary(SQLModel, table=True):

    # Table name
    __tablename__ = "librarian_library"


    # Foreign keys
    # Foreign key to dim_librarian table
    librarian_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_librarian.id", ondelete="CASCADE"),
            primary_key=True
        )
    )

    # Foreign key to dim_library table
    library_id: int = Field(
        sa_column=Column(
            ForeignKey("dim_library.id", ondelete="CASCADE"),
            primary_key=True
        )
    )