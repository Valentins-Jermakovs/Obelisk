# =====================================================
#                       imports
# =====================================================
from pydantic import BaseModel, Field
from typing import Optional
# =====================================================


# Language create schema 
class LanguageCreate(BaseModel):
    code: str = Field(min_length=2, max_length=10)
    name: Optional[str] = Field(default=None, max_length=100)

# Language read schema
class LanguageRead(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

# Language update schema
class LanguageUpdate(BaseModel):
    code: Optional[str] = Field(default=None, min_length=2, max_length=10)
    name: Optional[str] = Field(default=None, max_length=100)