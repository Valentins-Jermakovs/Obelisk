# ====================================================
#                       imports
# ====================================================
from pydantic import BaseModel, Field
# ===================================================

# Reader create
class ReaderCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=5, max_length=255)


# Reader update
class ReaderUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None


# Reader read
class ReaderRead(BaseModel):
    id: int
    full_name: str
    email: str