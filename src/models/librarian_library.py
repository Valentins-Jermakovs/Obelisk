# =====================================================
#                       imports
# =====================================================
from sqlmodel import SQLModel, Field
# =====================================================

# dim_librarian <-> librarian_library <-> dim_library (M2M)
class LibrarianLibrary(SQLModel, table=True):

    # Table name
    __tablename__ = "librarian_library"

    # Relationships
    librarian_id: int = Field(foreign_key="dim_librarian.id", primary_key=True)
    library_id: int = Field(foreign_key="dim_library.id", primary_key=True)