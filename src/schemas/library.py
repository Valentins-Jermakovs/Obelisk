# ===================================================
#                       imports
# ===================================================
from pydantic import BaseModel
# ===================================================


# ===================================================
#                       schemas
# ===================================================

# Library create schema
class LibraryCreate(BaseModel):
    name: str
    city: str
    address: str


# Library update schema
class LibraryUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None